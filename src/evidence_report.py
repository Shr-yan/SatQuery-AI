from __future__ import annotations

import base64
import html
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}

MAX_EMBEDDED_IMAGE_BYTES = (
    6 * 1024 * 1024
)

REPORT_LIMITATIONS = [
    (
        "Vision-language answers are qualitative. Exact scientific values "
        "should come from SatQuery's analysis tools and structured evidence."
    ),
    (
        "The EuroSAT scene specialist provides scene-level candidate scores. "
        "Its softmax scores are not calibrated confidence values and are not "
        "ground-truth land-cover labels."
    ),
    (
        "NDVI, NDWI and NDBI are spectral indicators, not guaranteed semantic "
        "classifications of vegetation, water or buildings."
    ),
    (
        "Uploaded bi-temporal visual-change percentages and thresholds are "
        "practical visual heuristics unless a scientific index/change workflow "
        "or reference mask is explicitly used."
    ),
    (
        "Optical-SAR fusion outputs are candidate evidence cues and are not "
        "calibrated water/building classifications."
    ),
]


def utc_now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


def _safe_json_value(
    value,
):
    try:
        json.dumps(
            value
        )
        return value
    except TypeError:
        return str(
            value
        )


def _sanitize_record(
    value,
):
    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _sanitize_record(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            _sanitize_record(
                item
            )
            for item in value
        ]

    return _safe_json_value(
        value
    )


def _escape(
    value,
):
    if value is None:
        return "-"

    return html.escape(
        str(value)
    )


def _flatten_simple(
    value,
    prefix="",
    max_rows=80,
):
    rows = []

    def visit(
        item,
        path,
    ):
        if len(rows) >= max_rows:
            return

        if isinstance(
            item,
            dict,
        ):
            for key, child in item.items():
                child_path = (
                    f"{path}.{key}"
                    if path
                    else str(key)
                )
                visit(
                    child,
                    child_path,
                )
            return

        if isinstance(
            item,
            list,
        ):
            if all(
                not isinstance(
                    child,
                    (dict, list),
                )
                for child in item
            ):
                rows.append(
                    (
                        path,
                        ", ".join(
                            str(child)
                            for child in item
                        ),
                    )
                )
            return

        rows.append(
            (
                path,
                item,
            )
        )

    visit(
        value,
        prefix,
    )

    return rows


def _path_from_image_reference(
    reference,
    project_root,
):
    if not isinstance(
        reference,
        str,
    ):
        return None

    text = reference.strip()

    if not text:
        return None

    if text.startswith(
        "/uploaded-image?"
    ) or text.startswith(
        "/result-image?"
    ):
        parsed = urlparse(
            text
        )
        query = parse_qs(
            parsed.query
        )
        values = query.get(
            "path"
        )
        if not values:
            return None
        text = values[0]

    path = Path(
        text
    )

    if not path.is_absolute():
        path = (
            Path(project_root)
            / path
        )

    try:
        resolved = path.resolve()
    except Exception:
        return None

    if resolved.suffix.lower() not in IMAGE_EXTENSIONS:
        return None

    if not resolved.exists() or not resolved.is_file():
        return None

    try:
        if resolved.stat().st_size > MAX_EMBEDDED_IMAGE_BYTES:
            return None
    except OSError:
        return None

    return resolved


def _collect_image_paths(
    value,
    project_root,
    limit=6,
):
    collected = []
    seen = set()

    def visit(
        item,
    ):
        if len(collected) >= limit:
            return

        if isinstance(
            item,
            dict,
        ):
            for child in item.values():
                visit(
                    child
                )
            return

        if isinstance(
            item,
            list,
        ):
            for child in item:
                visit(
                    child
                )
            return

        path = _path_from_image_reference(
            item,
            project_root,
        )

        if path is None:
            return

        key = str(
            path
        )

        if key in seen:
            return

        seen.add(
            key
        )
        collected.append(
            path
        )

    visit(
        value
    )

    return collected


def _image_data_url(
    path,
):
    path = Path(
        path
    )

    mime_type = mimetypes.guess_type(
        path.name
    )[0]

    if mime_type not in {
        "image/png",
        "image/jpeg",
    }:
        return None

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode(
        "ascii"
    )

    return (
        f"data:{mime_type};base64,{encoded}"
    )


def _report_focus(
    workflow,
    record,
):
    execution = record.get(
        "execution_summary",
        {}
    )

    message = (
        record.get("message")
        or record.get("answer")
        or record.get("latest_answer")
        or "SatQuery evidence bundle"
    )

    return {
        "Workflow": workflow.replace(
            "_",
            " "
        ),
        "Task": execution.get(
            "task",
            record.get(
                "task",
                "-",
            ),
        ),
        "Controller": execution.get(
            "controller",
            "SatQuery Agent Controller",
        ),
        "Status": execution.get(
            "status",
            "completed",
        ),
        "Summary": message,
    }


def create_evidence_report(
    reports_dir,
    project_root,
    report_id,
    workflow,
    title,
    record,
    registry_snapshot,
    specialist_status=None,
):
    reports_dir = Path(
        reports_dir
    )
    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_at = utc_now_iso()
    safe_record = _sanitize_record(
        record
    )
    safe_registry = _sanitize_record(
        registry_snapshot
    )
    safe_specialist = _sanitize_record(
        specialist_status or {}
    )

    report_title = (
        title.strip()
        if isinstance(title, str)
        and title.strip()
        else "SatQuery AI Evidence Report"
    )

    bundle = {
        "report_id": report_id,
        "title": report_title,
        "generated_at": generated_at,
        "workflow": workflow,
        "evidence": safe_record,
        "model_tool_registry": safe_registry,
        "remote_sensing_specialist": safe_specialist,
        "interpretation_limitations": REPORT_LIMITATIONS,
    }

    json_path = (
        reports_dir
        / f"satquery_evidence_{report_id}.json"
    )

    json_path.write_text(
        json.dumps(
            bundle,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    focus = _report_focus(
        workflow,
        safe_record,
    )

    focus_rows = "".join(
        (
            "<tr>"
            f"<th>{_escape(key)}</th>"
            f"<td>{_escape(value)}</td>"
            "</tr>"
        )
        for key, value
        in focus.items()
    )

    execution = safe_record.get(
        "execution_summary",
        {}
    )

    execution_rows = _flatten_simple(
        execution,
        max_rows=45,
    )

    execution_html = "".join(
        (
            "<tr>"
            f"<th>{_escape(key.replace('_', ' '))}</th>"
            f"<td>{_escape(value)}</td>"
            "</tr>"
        )
        for key, value
        in execution_rows
    )

    evidence_rows = _flatten_simple(
        {
            key: value
            for key, value in safe_record.items()
            if key not in {
                "execution_summary",
                "conversation_history",
            }
        },
        max_rows=70,
    )

    evidence_html = "".join(
        (
            "<tr>"
            f"<th>{_escape(key.replace('_', ' '))}</th>"
            f"<td>{_escape(value)}</td>"
            "</tr>"
        )
        for key, value
        in evidence_rows
    )

    image_cards = []

    for path in _collect_image_paths(
        safe_record,
        project_root,
    ):
        try:
            data_url = _image_data_url(
                path
            )
        except Exception:
            data_url = None

        if not data_url:
            continue

        image_cards.append(
            (
                '<figure class="image-card">'
                f'<img src="{data_url}" alt="SatQuery visual evidence">'
                f'<figcaption>{_escape(path.name)}</figcaption>'
                "</figure>"
            )
        )

    image_section = (
        "".join(
            image_cards
        )
        if image_cards
        else (
            '<p class="muted">No local visual file was available for embedding in this report.</p>'
        )
    )

    limitations_html = "".join(
        f"<li>{_escape(item)}</li>"
        for item in REPORT_LIMITATIONS
    )

    full_json = html.escape(
        json.dumps(
            safe_record,
            indent=2,
            ensure_ascii=False,
        )
    )

    registry_json = html.escape(
        json.dumps(
            safe_registry,
            indent=2,
            ensure_ascii=False,
        )
    )

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(report_title)}</title>
<style>
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f7fb; color: #172033; line-height: 1.5; }}
    .page {{ width: min(1100px, 94%); margin: 34px auto 60px; }}
    .hero {{ background: linear-gradient(135deg, #102a43, #1f5f8b); color: white; padding: 28px; border-radius: 16px; }}
    .hero h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .hero p {{ margin: 4px 0; opacity: .9; }}
    section {{ background: white; padding: 22px; border-radius: 14px; margin-top: 20px; box-shadow: 0 8px 24px rgba(20, 36, 60, .08); }}
    h2 {{ margin-top: 0; font-size: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; vertical-align: top; padding: 9px 10px; border-bottom: 1px solid #e6edf5; overflow-wrap: anywhere; }}
    th {{ width: 32%; color: #46637f; font-weight: 700; }}
    .visual-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }}
    .image-card {{ margin: 0; background: #f8fafc; border: 1px solid #e2eaf2; border-radius: 12px; padding: 10px; }}
    .image-card img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
    figcaption {{ font-size: 12px; color: #60758a; margin-top: 7px; }}
    .pill {{ display: inline-block; padding: 5px 10px; border-radius: 999px; background: #dff2ff; color: #135a85; font-weight: 700; font-size: 12px; }}
    .muted {{ color: #66788a; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e6edf7; padding: 16px; border-radius: 10px; max-height: 520px; overflow: auto; }}
    ul {{ padding-left: 22px; }}
    footer {{ color: #617386; font-size: 12px; margin-top: 24px; text-align: center; }}
    @media print {{ body {{ background: white; }} section, .hero {{ box-shadow: none; break-inside: avoid; }} .page {{ width: 100%; margin: 0; }} }}
</style>
</head>
<body>
<div class="page">
    <div class="hero">
        <span class="pill">AUDITABLE EVIDENCE</span>
        <h1>{_escape(report_title)}</h1>
        <p>Generated by SatQuery AI</p>
        <p>{_escape(generated_at)}</p>
    </div>

    <section>
        <h2>Result Overview</h2>
        <table>{focus_rows}</table>
    </section>

    <section>
        <h2>Observable Execution Summary</h2>
        <p class="muted">This section contains the exposed task routing, selected models/tools and permitted parameters. It is not hidden chain-of-thought.</p>
        <table>{execution_html or '<tr><td>No execution summary was present.</td></tr>'}</table>
    </section>

    <section>
        <h2>Key Evidence</h2>
        <table>{evidence_html or '<tr><td>No structured evidence was present.</td></tr>'}</table>
    </section>

    <section>
        <h2>Visual Evidence</h2>
        <div class="visual-grid">{image_section}</div>
    </section>

    <section>
        <h2>Interpretation Limits</h2>
        <ul>{limitations_html}</ul>
    </section>

    <section>
        <h2>Model / Tool Registry Snapshot</h2>
        <pre>{registry_json}</pre>
    </section>

    <section>
        <h2>Full Structured Evidence</h2>
        <pre>{full_json}</pre>
    </section>

    <footer>SatQuery AI evidence report · Report ID {_escape(report_id)}</footer>
</div>
</body>
</html>"""

    html_path = (
        reports_dir
        / f"satquery_evidence_{report_id}.html"
    )

    html_path.write_text(
        report_html,
        encoding="utf-8",
    )

    return {
        "report_id": report_id,
        "html_path": html_path,
        "json_path": json_path,
        "generated_at": generated_at,
        "embedded_image_count": len(
            image_cards
        ),
    }
