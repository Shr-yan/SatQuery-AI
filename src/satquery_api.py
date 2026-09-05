from pathlib import Path
from typing import Any
from uuid import uuid4
from time import perf_counter
import json
import re
import shutil


from fastapi.staticfiles import (
    StaticFiles,
)

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    FileResponse,
)

from pydantic import (
    BaseModel,
    Field,
)

from ai_assistant import (
    SatQueryAssistant,
)

from satquery_service import (
    execute_query,
)

from vision_assistant import (
    SatQueryVisionAssistant,
)

from vision_context import (
    choose_vision_image,
)

from uploaded_imagery import (
    SUPPORTED_UPLOAD_EXTENSIONS,
    inspect_uploaded_image,
)

from uploaded_change import (
    create_visual_change_outputs,
    validate_pair,
)

from uploaded_crossmodal import (
    create_crossmodal_outputs,
    validate_crossmodal_pair,
)

from remote_sensing_specialist import (
    predict_scene,
    specialist_status,
)

from agent_registry import (
    get_registry_snapshot,
)

from agent_orchestrator import (
    ORCHESTRATOR_VERSION,
    build_search_earth_plan,
    route_uploaded_task,
)

from evidence_report import (
    create_evidence_report,
)

from evaluation_logger import (
    get_evaluation_summary,
    log_api_event,
)

from benchmark_evaluator import (
    IMPLEMENTATION_READINESS,
    evaluate_records,
    get_benchmark_summary,
    load_demo_cases,
    save_benchmark_run,
)

from public_benchmark_results import (
    get_public_benchmark_summary,
    save_public_benchmark_run,
    validate_public_benchmark_run,
)

from runtime_maintenance import (
    maybe_cleanup_runtime_artifacts,
    runtime_storage_status,
)

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

WEB_DIR = (
    PROJECT_ROOT
    / "web"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "results"
)

UPLOADS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "uploads"
)

REPORTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reports"
)

EVALUATION_LOG_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "evaluation"
    / "execution_log.jsonl"
)

BENCHMARK_RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "evaluation"
    / "benchmark_runs"
)

PUBLIC_BENCHMARK_RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "evaluation"
    / "public_benchmark_runs"
)

DEMO_CASES_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "sih_demo_cases.json"
)

MAX_UPLOAD_BYTES = (
    30 * 1024 * 1024
)

APP_VERSION = "1.5.0"

UPLOADS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app = FastAPI(
    title="SatQuery AI API",
    description=(
        "Natural-language Sentinel-2 "
        "satellite imagery, scientific "
        "analysis and grounded AI "
        "follow-up assistant."
    ),
    version=APP_VERSION,
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(
            WEB_DIR
        )
    ),
    name="static",
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "*"
    ],

    allow_credentials=False,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


@app.middleware("http")
async def deployment_security_headers(
    request: Request,
    call_next,
):
    """Add conservative browser security headers without changing the UI.

    We intentionally do not add a strict Content-Security-Policy here because
    the current SatQuery UI uses data/blob URLs for generated evidence and a
    too-strict policy could break working image/report flows.
    """
    response = await call_next(request)
    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff",
    )
    response.headers.setdefault(
        "X-Frame-Options",
        "SAMEORIGIN",
    )
    response.headers.setdefault(
        "Referrer-Policy",
        "no-referrer",
    )
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    return response


@app.middleware("http")
async def evaluation_audit_middleware(
    request: Request,
    call_next,
):
    # Deployment housekeeping is opportunistic and rate-limited. Failure to
    # clean temporary artifacts must never block a user request.
    try:
        maybe_cleanup_runtime_artifacts(
            uploads_dir=UPLOADS_DIR,
            reports_dir=REPORTS_DIR,
        )
    except Exception:
        pass

    started = perf_counter()

    try:
        response = await call_next(
            request
        )
    except Exception:
        duration_ms = (
            perf_counter()
            - started
        ) * 1000.0

        log_api_event(
            log_path=EVALUATION_LOG_PATH,
            path=request.url.path,
            method=request.method,
            status_code=500,
            duration_ms=duration_ms,
        )
        raise

    duration_ms = (
        perf_counter()
        - started
    ) * 1000.0

    log_api_event(
        log_path=EVALUATION_LOG_PATH,
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    return response


class QueryRequest(
    BaseModel
):

    query: str = Field(
        ...,
        min_length=3,
        description=(
            "Natural-language "
            "satellite-analysis query."
        ),
    )

class VisionRequest(
    BaseModel
):

    question: str = Field(
        ...,
        min_length=2,
    )

    analysis_result: dict[
        str,
        Any
    ]


class ChatMessage(
    BaseModel
):

    role: str

    content: str


class UploadedVisionRequest(
    BaseModel
):

    upload_id: str = Field(
        ...,
        min_length=32,
        max_length=32,
        pattern=r"^[a-f0-9]{32}$",
    )

    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
    )

    conversation_history: list[
        ChatMessage
    ] = []


class UploadedChangeVisionRequest(
    BaseModel
):

    pair_id: str = Field(
        ...,
        min_length=32,
        max_length=32,
        pattern=r"^[a-f0-9]{32}$",
    )

    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
    )

    conversation_history: list[
        ChatMessage
    ] = []


class UploadedCrossModalVisionRequest(
    BaseModel
):

    pair_id: str = Field(
        ...,
        min_length=32,
        max_length=32,
        pattern=r"^[a-f0-9]{32}$",
    )

    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
    )

    conversation_history: list[
        ChatMessage
    ] = []


class ChatRequest(
    BaseModel
):

    question: str = Field(
        ...,
        min_length=2,
        description=(
            "Follow-up question about "
            "the current SatQuery result."
        ),
    )

    analysis_result: dict[
        str,
        Any
    ]

    conversation_history: list[
        ChatMessage
    ] = []


class EvidenceReportRequest(
    BaseModel
):

    workflow: str = Field(
        ...,
        min_length=3,
        max_length=80,
    )

    title: str | None = Field(
        default=None,
        max_length=160,
    )

    record: dict[
        str,
        Any
    ]


class BenchmarkRecord(
    BaseModel
):

    case_id: str | None = None
    task: str = Field(default="unspecified", max_length=80)
    category: str | None = Field(default=None, max_length=120)
    source: str | None = Field(default=None, max_length=160)
    question: str | None = Field(default=None, max_length=2000)
    reference_answer: str = Field(..., max_length=4000)
    model_answer: str = Field(..., max_length=4000)


class BenchmarkEvaluationRequest(
    BaseModel
):

    records: list[BenchmarkRecord] = Field(
        ...,
        min_length=1,
        max_length=5000,
    )


class PublicBenchmarkImportRequest(
    BaseModel
):

    result: dict[
        str,
        Any
    ]


@app.get("/")
def root():

    return {
        "name":
        "SatQuery AI",

        "status":
        "running",

        "version":
        APP_VERSION,

        "web_app":
        "/app",

        "documentation":
        "/docs",

        "supported_analysis": [
            "Sentinel-2 RGB imagery",
            "NDVI",
            "vegetation",
            "NDWI",
            "water",
            "NDBI",
            "urban",
            "two-date change analysis",
            "vegetation trend analysis",
            "grounded AI follow-up chat",
            "uploaded remote-sensing image validation",
            "uploaded image preview generation",
            "uploaded-image VQA",
            "uploaded-image scene captioning",
            "uploaded-image follow-up vision chat",
            "EuroSAT-trained remote-sensing scene specialist",
            "observable specialist model registry",
            "unified agentic task routing",
            "auditable routing factors and selected-component trace",
            "uploaded bi-temporal pair validation",
            "uploaded change map",
            "uploaded change VQA",
            "uploaded optical-SAR pair validation",
            "cross-modal optical-SAR evidence map",
            "optical-SAR joint VQA",
            "downloadable HTML evidence reports",
            "downloadable JSON evidence bundles",
            "privacy-conscious evaluation execution logging",
            "SIH evaluation readiness center",
            "local benchmark proxy evaluator (exact match + token F1)",
            "public VRSBench subset result import and audit",
            "public CDVQA subset result import and audit",
            "age-based cleanup of temporary uploads and reports",
        ],
    }


@app.get("/health")
def health():

    return {
        "status":
        "healthy",

        "version":
        APP_VERSION,
    }


@app.get("/ready")
def ready():
    """Release-readiness check that does not load heavyweight models."""
    web_ready = (
        WEB_DIR
        / "index.html"
    ).exists()

    specialist = specialist_status()
    specialist_ready = bool(
        specialist.get(
            "available"
        )
    )

    checks = {
        "web_interface":
        web_ready,

        "remote_sensing_specialist":
        specialist_ready,

        "demo_cases":
        DEMO_CASES_PATH.exists(),
    }

    return {
        "ready":
        all(checks.values()),

        "version":
        APP_VERSION,

        "checks":
        checks,

        "note": (
            "This readiness route verifies release-critical local artifacts "
            "without loading the TorchScript model or calling external APIs."
        ),
    }


@app.get("/runtime-status")
def runtime_status():

    return {
        "success": True,
        "service": "SatQuery AI",
        "version": APP_VERSION,
        "temporary_artifacts": runtime_storage_status(
            uploads_dir=UPLOADS_DIR,
            reports_dir=REPORTS_DIR,
        ),
        "remote_sensing_specialist": specialist_status(),
        "notes": [
            "The EuroSAT TorchScript specialist is loaded lazily on first use.",
            "Temporary uploads and generated reports are cleaned by age.",
            "Evaluation logs and imported benchmark results are not deleted by runtime cleanup.",
        ],
    }


@app.get("/model-registry")
def model_registry():

    return {
        "success": True,
        "controller": "SatQuery Agent Controller",
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "registry": get_registry_snapshot(),
        "remote_sensing_specialist": specialist_status(),
    }


@app.get("/evaluation-summary")
def evaluation_summary():

    return {
        "success": True,
        "logger": "SatQuery Evaluation Logger",
        "privacy_note": (
            "The execution log stores route, outcome and timing metadata only; "
            "it does not store prompts, chat text, uploaded image bytes or API keys."
        ),
        **get_evaluation_summary(
            EVALUATION_LOG_PATH
        ),
    }


@app.get("/evaluation")
def evaluation_center_page():

    page = WEB_DIR / "evaluation.html"

    if not page.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation Center page was not found.",
        )

    return FileResponse(page)


@app.get("/evaluation-center-data")
def evaluation_center_data():

    return {
        "success": True,
        "implementation_readiness": IMPLEMENTATION_READINESS,
        "runtime_summary": get_evaluation_summary(EVALUATION_LOG_PATH),
        "remote_sensing_specialist": specialist_status(),
        "benchmark_summary": get_benchmark_summary(BENCHMARK_RESULTS_DIR),
        "public_benchmark_summary": get_public_benchmark_summary(
            PUBLIC_BENCHMARK_RESULTS_DIR
        ),
        "demo_cases": load_demo_cases(DEMO_CASES_PATH),
        "registry": get_registry_snapshot(),
        "note": (
            "Implementation readiness is not the same as official benchmark performance. "
            "The local proxy evaluator is for development evidence only."
        ),
    }


@app.get("/public-benchmark-summary")
def public_benchmark_summary():

    return {
        "success": True,
        **get_public_benchmark_summary(
            PUBLIC_BENCHMARK_RESULTS_DIR
        ),
    }


@app.post("/public-benchmark-import")
def public_benchmark_import(
    request: PublicBenchmarkImportRequest,
):

    try:
        cleaned = validate_public_benchmark_run(
            request.result
        )

        output_path = save_public_benchmark_run(
            PUBLIC_BENCHMARK_RESULTS_DIR,
            cleaned,
        )

        return {
            "success": True,
            "saved_path": str(output_path),
            "summary": get_public_benchmark_summary(
                PUBLIC_BENCHMARK_RESULTS_DIR
            ),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "public_benchmark_input_invalid",
                "message": str(error),
            },
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "public_benchmark_import_failed",
                "message": str(error),
            },
        )


@app.get("/benchmark-summary")
def benchmark_summary():

    return {
        "success": True,
        **get_benchmark_summary(BENCHMARK_RESULTS_DIR),
    }


@app.post("/benchmark-evaluate")
def benchmark_evaluate(
    request: BenchmarkEvaluationRequest,
):

    try:
        records = [
            record.model_dump()
            for record in request.records
        ]

        result = evaluate_records(records)
        output_path = save_benchmark_run(
            BENCHMARK_RESULTS_DIR,
            result,
        )

        return {
            "success": True,
            "result": result,
            "saved_path": str(output_path),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "benchmark_input_invalid",
                "message": str(error),
            },
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "benchmark_evaluation_failed",
                "message": str(error),
            },
        )


@app.post("/evidence-report")
def evidence_report(
    request: EvidenceReportRequest,
):

    workflow = (
        request.workflow
        .strip()
        .lower()
        .replace(" ", "_")
    )

    allowed_workflows = {
        "search_earth",
        "single_image",
        "bitemporal_pair",
        "optical_sar_pair",
    }

    if workflow not in allowed_workflows:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "unsupported_report_workflow",
                "message": (
                    "Evidence reports support Search Earth, single image, "
                    "bi-temporal pair and optical-SAR pair workflows."
                ),
            },
        )

    report_id = uuid4().hex

    try:
        result = create_evidence_report(
            reports_dir=REPORTS_DIR,
            project_root=PROJECT_ROOT,
            report_id=report_id,
            workflow=workflow,
            title=request.title,
            record=request.record,
            registry_snapshot=get_registry_snapshot(),
            specialist_status=specialist_status(),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "evidence_report_failed",
                "message": str(error),
            },
        )

    return {
        "success": True,
        "report_id": report_id,
        "generated_at": result["generated_at"],
        "embedded_image_count": result["embedded_image_count"],
        "html_url": (
            "/download-evidence-report?report_id="
            + report_id
            + "&format=html"
        ),
        "json_url": (
            "/download-evidence-report?report_id="
            + report_id
            + "&format=json"
        ),
    }


@app.get("/download-evidence-report")
def download_evidence_report(
    report_id: str,
    format: str = "html",
):

    if not re.fullmatch(
        r"[a-f0-9]{32}",
        report_id or "",
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid report ID.",
        )

    report_format = (
        format
        .strip()
        .lower()
    )

    if report_format not in {
        "html",
        "json",
    }:
        raise HTTPException(
            status_code=400,
            detail="Report format must be html or json.",
        )

    suffix = (
        ".html"
        if report_format == "html"
        else ".json"
    )

    report_path = (
        REPORTS_DIR
        / f"satquery_evidence_{report_id}{suffix}"
    ).resolve()

    try:
        report_path.relative_to(
            REPORTS_DIR.resolve()
        )
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Report path is outside the reports directory.",
        )

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Evidence report was not found.",
        )

    media_type = (
        "text/html"
        if report_format == "html"
        else "application/json"
    )

    return FileResponse(
        report_path,
        media_type=media_type,
        filename=report_path.name,
    )


@app.get("/app")
def web_app():

    index_file = (
        WEB_DIR
        / "index.html"
    )

    if not index_file.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "SatQuery web interface "
                "was not found."
            ),
        )

    return FileResponse(
        index_file
    )



@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
):

    filename = Path(
        file.filename or "uploaded_image"
    ).name

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "unsupported_upload_type",

                "message": (
                    "Unsupported file type. Use "
                    "GeoTIFF/TIFF, PNG, JPG or JPEG."
                ),
            },
        )

    upload_id = uuid4().hex

    upload_folder = (
        UPLOADS_DIR
        / upload_id
    )

    upload_folder.mkdir(
        parents=True,
        exist_ok=False,
    )

    original_path = (
        upload_folder
        / ("original" + extension)
    )

    preview_path = (
        upload_folder
        / "preview.png"
    )

    size_bytes = 0

    try:

        with original_path.open("wb") as output:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                size_bytes += len(chunk)

                if size_bytes > MAX_UPLOAD_BYTES:

                    raise HTTPException(
                        status_code=413,
                        detail={
                            "type":
                            "upload_too_large",

                            "message": (
                                "Uploaded image exceeds "
                                "the 30 MB limit."
                            ),
                        },
                    )

                output.write(chunk)

        if size_bytes == 0:

            raise HTTPException(
                status_code=400,
                detail={
                    "type":
                    "empty_upload",

                    "message":
                    "The uploaded file is empty.",
                },
            )

        metadata = inspect_uploaded_image(
            original_path,
            preview_path,
        )

        metadata["filename"] = filename
        metadata["size_bytes"] = size_bytes

        metadata_path = (
            upload_folder
            / "metadata.json"
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        preview_relative = (
            preview_path
            .relative_to(
                PROJECT_ROOT
            )
            .as_posix()
        )

        return {
            "success":
            True,

            "upload_id":
            upload_id,

            "input":
            metadata,

            "preview_url": (
                "/uploaded-image?path="
                + preview_relative
            ),

            "message": (
                "The uploaded image passed "
                "basic format and readability validation."
            ),

            "execution_summary": {
                **route_uploaded_task(
                    input_configuration={
                        "kind": "single_image",
                        "input_count": 1,
                        "modalities": [
                            metadata.get(
                                "modality_hint"
                            )
                        ],
                    },
                    stage="validation",
                    input_metadata=metadata,
                ),
                "status": "completed",
            },
        }

    except HTTPException:

        shutil.rmtree(
            upload_folder,
            ignore_errors=True,
        )

        raise

    except Exception as error:

        shutil.rmtree(
            upload_folder,
            ignore_errors=True,
        )

        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "invalid_uploaded_image",

                "message":
                str(error),
            },
        )

    finally:

        await file.close()


@app.get("/uploaded-image")
def uploaded_image(
    path: str,
):

    requested_path = Path(
        path
    )

    if not requested_path.is_absolute():

        requested_path = (
            PROJECT_ROOT
            / requested_path
        )

    allowed_root = (
        UPLOADS_DIR.resolve()
    )

    resolved_path = (
        requested_path.resolve()
    )

    try:

        resolved_path.relative_to(
            allowed_root
        )

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail=(
                "Requested upload preview is "
                "outside the uploads directory."
            ),
        )

    if not resolved_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Uploaded image preview was not found."
            ),
        )

    if resolved_path.suffix.lower() not in {
        ".png",
        ".jpg",
        ".jpeg",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only generated upload previews "
                "may be served."
            ),
        )

    return FileResponse(
        resolved_path
    )

@app.post("/uploaded-vision-chat")
def uploaded_vision_chat(
    request: UploadedVisionRequest,
):

    upload_folder = (
        UPLOADS_DIR
        / request.upload_id
    )

    preview_path = (
        upload_folder
        / "preview.png"
    )

    metadata_path = (
        upload_folder
        / "metadata.json"
    )

    if (
        not upload_folder.exists()
        or not preview_path.exists()
        or not metadata_path.exists()
    ):

        raise HTTPException(
            status_code=404,
            detail={
                "type":
                "uploaded_image_not_found",

                "message": (
                    "The validated uploaded image is no longer available. "
                    "Please upload it again."
                ),
            },
        )

    try:

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        history = [
            {
                "role":
                message.role,

                "content":
                message.content,
            }
            for message
            in request.conversation_history[-10:]
            if message.role
            in {
                "user",
                "assistant",
            }
        ]

        specialist_result = (
            predict_scene(
                image_path=preview_path,
                input_metadata=metadata,
                top_k=3,
            )
        )

        plan = (
            route_uploaded_task(
                input_configuration={
                    "kind": "single_image",
                    "input_count": 1,
                    "modalities": [
                        metadata.get(
                            "modality_hint"
                        )
                    ],
                },
                question=request.question,
                stage="analysis",
                specialist_available=(
                    specialist_result.get(
                        "available",
                        False,
                    )
                ),
                input_metadata=metadata,
            )
        )

        assistant = (
            SatQueryVisionAssistant()
        )

        answer = (
            assistant.analyze_uploaded_image(
                question=(
                    request.question
                ),

                image_path=(
                    preview_path
                ),

                input_metadata=(
                    metadata
                ),

                specialist_evidence=(
                    specialist_result
                ),

                conversation_history=(
                    history
                ),
            )
        )

        task = plan[
            "task"
        ]

        return {
            "success":
            True,

            "answer":
            answer,

            "upload_id":
            request.upload_id,

            "task":
            task,

            "specialist_evidence":
            specialist_result,

            "execution_summary": {
                **plan,
                "input": {
                    "format": metadata.get(
                        "format"
                    ),
                    "bands": metadata.get(
                        "bands"
                    ),
                    "crs": metadata.get(
                        "crs"
                    ),
                },
                "conversation_turns_used": len(
                    history
                ),
                "status": "completed",
            },
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail={
                "type":
                "uploaded_vision_failed",

                "message":
                str(error),
            },
        )


async def _save_pair_file(
    upload_file,
    destination,
):
    size_bytes = 0

    with destination.open("wb") as output:
        while True:
            chunk = await upload_file.read(
                1024 * 1024
            )

            if not chunk:
                break

            size_bytes += len(chunk)

            if size_bytes > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail={
                        "type":
                        "upload_too_large",

                        "message": (
                            "Each uploaded image must be 30 MB or smaller."
                        ),
                    },
                )

            output.write(chunk)

    if size_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "empty_upload",

                "message":
                "One of the uploaded files is empty.",
            },
        )

    return size_bytes


@app.post("/upload-change-pair")
async def upload_change_pair(
    before_file: UploadFile = File(...),
    after_file: UploadFile = File(...),
):
    before_name = Path(
        before_file.filename or "before_image"
    ).name
    after_name = Path(
        after_file.filename or "after_image"
    ).name

    before_extension = Path(
        before_name
    ).suffix.lower()
    after_extension = Path(
        after_name
    ).suffix.lower()

    if (
        before_extension not in SUPPORTED_UPLOAD_EXTENSIONS
        or after_extension not in SUPPORTED_UPLOAD_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "unsupported_upload_type",

                "message": (
                    "Both inputs must be GeoTIFF/TIFF, PNG, JPG or JPEG."
                ),
            },
        )

    pair_id = uuid4().hex
    pair_folder = (
        UPLOADS_DIR
        / pair_id
    )
    pair_folder.mkdir(
        parents=True,
        exist_ok=False,
    )

    before_path = (
        pair_folder
        / ("before" + before_extension)
    )
    after_path = (
        pair_folder
        / ("after" + after_extension)
    )
    before_preview_path = (
        pair_folder
        / "before_preview.png"
    )
    after_preview_path = (
        pair_folder
        / "after_preview.png"
    )
    change_map_path = (
        pair_folder
        / "change_map.png"
    )
    composite_path = (
        pair_folder
        / "change_composite.png"
    )

    try:
        before_size = await _save_pair_file(
            before_file,
            before_path,
        )
        after_size = await _save_pair_file(
            after_file,
            after_path,
        )

        before_meta = inspect_uploaded_image(
            before_path,
            before_preview_path,
        )
        after_meta = inspect_uploaded_image(
            after_path,
            after_preview_path,
        )

        before_meta["filename"] = before_name
        before_meta["size_bytes"] = before_size
        after_meta["filename"] = after_name
        after_meta["size_bytes"] = after_size

        pair_validation = validate_pair(
            before_path,
            after_path,
            before_meta,
            after_meta,
        )

        if not pair_validation["compatible"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "type":
                    "incompatible_change_pair",

                    "message":
                    pair_validation["message"],
                },
            )

        change_stats = create_visual_change_outputs(
            before_preview_path,
            after_preview_path,
            change_map_path,
            composite_path,
        )

        pair_metadata = {
            "pair_id":
            pair_id,

            "before":
            before_meta,

            "after":
            after_meta,

            "pair_validation":
            pair_validation,

            "visual_change":
            change_stats,
        }

        metadata_path = (
            pair_folder
            / "pair_metadata.json"
        )
        metadata_path.write_text(
            json.dumps(
                pair_metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        def upload_url(path):
            relative = (
                path
                .relative_to(
                    PROJECT_ROOT
                )
                .as_posix()
            )
            return (
                "/uploaded-image?path="
                + relative
            )

        return {
            "success":
            True,

            "pair_id":
            pair_id,

            "before":
            before_meta,

            "after":
            after_meta,

            "pair_validation":
            pair_validation,

            "visual_change":
            change_stats,

            "outputs": {
                "before_preview":
                upload_url(
                    before_preview_path
                ),

                "after_preview":
                upload_url(
                    after_preview_path
                ),

                "change_map":
                upload_url(
                    change_map_path
                ),
            },

            "execution_summary": {
                **route_uploaded_task(
                    input_configuration={
                        "kind": "bitemporal_pair",
                        "input_count": 2,
                        "modalities": [
                            "before_observation",
                            "after_observation",
                        ],
                        "visual_change_threshold": (
                            change_stats.get(
                                "visual_change_threshold"
                            )
                        ),
                    },
                    stage="validation",
                ),
                "status": "completed",
            },
        }

    except HTTPException:
        shutil.rmtree(
            pair_folder,
            ignore_errors=True,
        )
        raise

    except Exception as error:
        shutil.rmtree(
            pair_folder,
            ignore_errors=True,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "change_pair_failed",

                "message":
                str(error),
            },
        )

    finally:
        await before_file.close()
        await after_file.close()


@app.post("/uploaded-change-chat")
def uploaded_change_chat(
    request: UploadedChangeVisionRequest,
):
    pair_folder = (
        UPLOADS_DIR
        / request.pair_id
    )
    metadata_path = (
        pair_folder
        / "pair_metadata.json"
    )
    composite_path = (
        pair_folder
        / "change_composite.png"
    )

    if (
        not pair_folder.exists()
        or not metadata_path.exists()
        or not composite_path.exists()
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "type":
                "uploaded_change_pair_not_found",

                "message": (
                    "The uploaded before/after pair is no longer available. "
                    "Please upload it again."
                ),
            },
        )

    try:
        pair_metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        history = [
            {
                "role":
                message.role,

                "content":
                message.content,
            }
            for message
            in request.conversation_history[-10:]
            if message.role
            in {
                "user",
                "assistant",
            }
        ]

        assistant = (
            SatQueryVisionAssistant()
        )

        answer = (
            assistant.analyze_uploaded_change_pair(
                question=(
                    request.question
                ),

                composite_path=(
                    composite_path
                ),

                pair_metadata=(
                    pair_metadata
                ),

                conversation_history=(
                    history
                ),
            )
        )

        return {
            "success":
            True,

            "answer":
            answer,

            "pair_id":
            request.pair_id,

            "task":
            "bi_temporal_change_vqa",

            "execution_summary": {
                **route_uploaded_task(
                    input_configuration={
                        "kind": "bitemporal_pair",
                        "input_count": 2,
                        "modalities": [
                            "before_observation",
                            "after_observation",
                        ],
                        "visual_change_threshold": (
                            pair_metadata.get(
                                "visual_change",
                                {}
                            ).get(
                                "visual_change_threshold"
                            )
                        ),
                    },
                    question=request.question,
                    stage="analysis",
                ),
                "conversation_turns_used": len(
                    history
                ),
                "status": "completed",
            },
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "type":
                "uploaded_change_vqa_failed",

                "message":
                str(error),
            },
        )


@app.post("/upload-crossmodal-pair")
async def upload_crossmodal_pair(
    optical_file: UploadFile = File(...),
    sar_file: UploadFile = File(...),
):
    optical_name = Path(
        optical_file.filename or "optical_image"
    ).name
    sar_name = Path(
        sar_file.filename or "sar_image"
    ).name

    optical_extension = Path(
        optical_name
    ).suffix.lower()
    sar_extension = Path(
        sar_name
    ).suffix.lower()

    if (
        optical_extension not in SUPPORTED_UPLOAD_EXTENSIONS
        or sar_extension not in SUPPORTED_UPLOAD_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "unsupported_upload_type",

                "message": (
                    "Both inputs must be GeoTIFF/TIFF, PNG, JPG or JPEG."
                ),
            },
        )

    pair_id = uuid4().hex
    pair_folder = (
        UPLOADS_DIR
        / pair_id
    )
    pair_folder.mkdir(
        parents=True,
        exist_ok=False,
    )

    optical_path = (
        pair_folder
        / ("optical" + optical_extension)
    )
    sar_path = (
        pair_folder
        / ("sar" + sar_extension)
    )
    optical_preview_path = (
        pair_folder
        / "optical_preview.png"
    )
    sar_preview_path = (
        pair_folder
        / "sar_preview.png"
    )
    fusion_map_path = (
        pair_folder
        / "crossmodal_evidence.png"
    )
    composite_path = (
        pair_folder
        / "crossmodal_composite.png"
    )

    try:
        optical_size = await _save_pair_file(
            optical_file,
            optical_path,
        )
        sar_size = await _save_pair_file(
            sar_file,
            sar_path,
        )

        optical_meta = inspect_uploaded_image(
            optical_path,
            optical_preview_path,
        )
        sar_meta = inspect_uploaded_image(
            sar_path,
            sar_preview_path,
        )

        optical_meta["filename"] = optical_name
        optical_meta["size_bytes"] = optical_size
        optical_meta["declared_modality"] = "OPTICAL/MULTISPECTRAL"
        sar_meta["filename"] = sar_name
        sar_meta["size_bytes"] = sar_size
        sar_meta["declared_modality"] = "SAR"

        pair_validation = validate_crossmodal_pair(
            optical_path,
            sar_path,
            optical_meta,
            sar_meta,
        )

        if not pair_validation["compatible"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "type":
                    "incompatible_crossmodal_pair",

                    "message":
                    pair_validation["message"],
                },
            )

        fusion_stats = create_crossmodal_outputs(
            optical_preview_path,
            sar_preview_path,
            fusion_map_path,
            composite_path,
        )

        pair_metadata = {
            "pair_id":
            pair_id,

            "optical":
            optical_meta,

            "sar":
            sar_meta,

            "pair_validation":
            pair_validation,

            "crossmodal_evidence":
            fusion_stats,
        }

        metadata_path = (
            pair_folder
            / "crossmodal_metadata.json"
        )
        metadata_path.write_text(
            json.dumps(
                pair_metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        def upload_url(path):
            relative = (
                path
                .relative_to(
                    PROJECT_ROOT
                )
                .as_posix()
            )
            return (
                "/uploaded-image?path="
                + relative
            )

        return {
            "success":
            True,

            "pair_id":
            pair_id,

            "optical":
            optical_meta,

            "sar":
            sar_meta,

            "pair_validation":
            pair_validation,

            "crossmodal_evidence":
            fusion_stats,

            "outputs": {
                "optical_preview":
                upload_url(
                    optical_preview_path
                ),

                "sar_preview":
                upload_url(
                    sar_preview_path
                ),

                "fusion_map":
                upload_url(
                    fusion_map_path
                ),
            },

            "execution_summary": {
                **route_uploaded_task(
                    input_configuration={
                        "kind": "optical_sar_pair",
                        "input_count": 2,
                        "modalities": [
                            "optical_or_multispectral",
                            "sar",
                        ],
                    },
                    stage="validation",
                ),
                "status": "completed",
            },
        }

    except HTTPException:
        shutil.rmtree(
            pair_folder,
            ignore_errors=True,
        )
        raise

    except Exception as error:
        shutil.rmtree(
            pair_folder,
            ignore_errors=True,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "type":
                "crossmodal_pair_failed",

                "message":
                str(error),
            },
        )

    finally:
        await optical_file.close()
        await sar_file.close()


@app.post("/uploaded-crossmodal-chat")
def uploaded_crossmodal_chat(
    request: UploadedCrossModalVisionRequest,
):
    pair_folder = (
        UPLOADS_DIR
        / request.pair_id
    )
    metadata_path = (
        pair_folder
        / "crossmodal_metadata.json"
    )
    composite_path = (
        pair_folder
        / "crossmodal_composite.png"
    )

    if (
        not pair_folder.exists()
        or not metadata_path.exists()
        or not composite_path.exists()
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "type":
                "uploaded_crossmodal_pair_not_found",

                "message": (
                    "The uploaded optical-SAR pair is no longer available. "
                    "Please upload it again."
                ),
            },
        )

    try:
        pair_metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        history = [
            {
                "role":
                message.role,

                "content":
                message.content,
            }
            for message
            in request.conversation_history[-10:]
            if message.role
            in {
                "user",
                "assistant",
            }
        ]

        assistant = (
            SatQueryVisionAssistant()
        )

        answer = (
            assistant.analyze_uploaded_crossmodal_pair(
                question=(
                    request.question
                ),

                composite_path=(
                    composite_path
                ),

                pair_metadata=(
                    pair_metadata
                ),

                conversation_history=(
                    history
                ),
            )
        )

        return {
            "success":
            True,

            "answer":
            answer,

            "pair_id":
            request.pair_id,

            "task":
            "optical_sar_joint_vqa",

            "execution_summary": {
                **route_uploaded_task(
                    input_configuration={
                        "kind": "optical_sar_pair",
                        "input_count": 2,
                        "modalities": [
                            "optical_or_multispectral",
                            "sar",
                        ],
                    },
                    question=request.question,
                    stage="analysis",
                ),
                "conversation_turns_used": len(
                    history
                ),
                "status": "completed",
            },
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "type":
                "uploaded_crossmodal_vqa_failed",

                "message":
                str(error),
            },
        )


@app.post("/analyze")
def analyze(
    request: QueryRequest,
):

    response = execute_query(
        request.query
    )

    if not response[
        "success"
    ]:

        error = response[
            "error"
        ]

        raise HTTPException(
            status_code=400,
            detail={
                "type":
                error[
                    "type"
                ],

                "message":
                error[
                    "message"
                ],
            },
        )

    response[
        "execution_summary"
    ] = {
        **build_search_earth_plan(
            response
        ),
        "status": "completed",
    }

    return response


@app.post("/chat")
def chat(
    request: ChatRequest,
):

    try:

        assistant = (
            SatQueryAssistant()
        )

        history = [
            {
                "role":
                message.role,

                "content":
                message.content,
            }

            for message
            in request.conversation_history
        ]

        assistant_result = (
            assistant.answer(
                question=(
                    request.question
                ),

                analysis_result=(
                    request.analysis_result
                ),

                conversation_history=(
                    history
                ),
            )
        )


        return {
            "success":
            True,

            "answer":
            assistant_result[
                "answer"
            ],

            "tool_executed":
            assistant_result[
                "tool_executed"
            ],

            "tool_query":
            assistant_result[
                "tool_query"
            ],

            "analysis_result":
            assistant_result[
                "analysis_result"
            ],
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail={
                "type":
                "ai_assistant_failed",

                "message":
                str(
                    error
                ),
            },
        )

@app.post("/vision-chat")
def vision_chat(
    request: VisionRequest,
):

    try:

        image_type, image_path = (
            choose_vision_image(
                analysis_result=(
                    request.analysis_result
                ),

                question=(
                    request.question
                ),
            )
        )


        if (
            not image_type
            or not image_path
        ):

            raise HTTPException(
                status_code=400,
                detail={
                    "type":
                    "vision_image_not_found",

                    "message":
                    (
                        "No suitable generated "
                        "SatQuery image is "
                        "available for this result."
                    ),
                },
            )


        assistant = (
            SatQueryVisionAssistant()
        )


        answer = (
            assistant.analyze_image(
                question=(
                    request.question
                ),

                image_path=(
                    image_path
                ),

                analysis_result=(
                    request.analysis_result
                ),

                image_type=(
                    image_type
                ),
            )
        )


        return {
            "success":
            True,

            "answer":
            answer,

            "image_type":
            image_type,
        }


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail={
                "type":
                "vision_analysis_failed",

                "message":
                str(
                    error
                ),
            },
        )
    
@app.get("/result-image")
def result_image(
    path: str,
):

    requested_path = Path(
        path
    )

    if (
        not
        requested_path.is_absolute()
    ):

        requested_path = (
            PROJECT_ROOT
            / requested_path
        )

    allowed_root = (
        RESULTS_DIR.resolve()
    )

    resolved_path = (
        requested_path.resolve()
    )

    try:

        resolved_path.relative_to(
            allowed_root
        )

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail=(
                "Requested file is "
                "outside the results "
                "directory."
            ),
        )

    if not resolved_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Result file not found."
            ),
        )

    if (
        resolved_path.suffix.lower()
        not in {
            ".png",
            ".jpg",
            ".jpeg",
        }
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only generated image "
                "files may be served."
            ),
        )

    return FileResponse(
        resolved_path
    )


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "satquery_api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )