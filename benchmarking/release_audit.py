from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "data" / "processed" / "models" / "satquery_eurosat_specialist.pt"
METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "models" / "satquery_eurosat_metrics.json"

REQUIRED_FILES = [
    "src/satquery_api.py",
    "src/agent_orchestrator.py",
    "src/agent_registry.py",
    "src/remote_sensing_specialist.py",
    "src/vision_assistant.py",
    "src/uploaded_imagery.py",
    "src/uploaded_change.py",
    "src/uploaded_crossmodal.py",
    "src/evidence_report.py",
    "src/evaluation_logger.py",
    "src/benchmark_evaluator.py",
    "src/public_benchmark_results.py",
    "src/runtime_maintenance.py",
    "web/index.html",
    "web/app.js",
    "web/styles.css",
    "web/evaluation.html",
    "web/evaluation.js",
    "data/evaluation/sih_demo_cases.json",
    "requirements.txt",
    ".python-version",
    ".gitignore",
]

REQUIRED_REQUIREMENTS = {
    "fastapi",
    "uvicorn",
    "python-multipart",
    "groq",
    "torch",
    "rasterio",
    "planetary-computer",
    "pystac-client",
}

SECRET_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
}


def run_git(*args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def tracked_files() -> list[str] | None:
    code, output = run_git("ls-files")
    if code != 0:
        return None
    return [line.strip() for line in output.splitlines() if line.strip()]


def check_required_files(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (PROJECT_ROOT / relative).exists():
            errors.append(f"missing required file: {relative}")

    if not MODEL_PATH.exists():
        errors.append("missing EuroSAT specialist model")
    elif MODEL_PATH.stat().st_size > 10 * 1024 * 1024:
        errors.append(
            f"EuroSAT specialist unexpectedly large: {MODEL_PATH.stat().st_size / 1024 / 1024:.2f} MB"
        )

    if not METRICS_PATH.exists():
        errors.append("missing EuroSAT specialist metrics JSON")


def check_requirements(errors: list[str], warnings: list[str]) -> None:
    path = PROJECT_ROOT / "requirements.txt"
    if not path.exists():
        return
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split("==", 1)[0].split(">=", 1)[0].split("[", 1)[0].strip().lower()
        names.add(name)

    missing = sorted(REQUIRED_REQUIREMENTS - names)
    if missing:
        errors.append("requirements.txt missing: " + ", ".join(missing))

    if "python-dotenv" not in names:
        warnings.append("python-dotenv is not listed; local .env loading may fail")


def check_git(errors: list[str], warnings: list[str]) -> None:
    tracked = tracked_files()
    if tracked is None:
        warnings.append("git executable/repository unavailable; skipped tracked-file checks")
        return

    tracked_lower = {item.replace("\\", "/").lower() for item in tracked}

    for item in tracked:
        normalized = item.replace("\\", "/")
        lower = normalized.lower()
        basename = Path(normalized).name.lower()

        if basename in SECRET_NAMES or lower.endswith((".pem", ".key")):
            errors.append(f"secret/private-key file is tracked: {normalized}")

        if "__pycache__/" in lower or lower.endswith((".pyc", ".pyo")):
            warnings.append(f"Python cache file is tracked: {normalized}")

        path = PROJECT_ROOT / normalized
        try:
            size = path.stat().st_size
        except OSError:
            continue

        if size >= 95 * 1024 * 1024:
            errors.append(
                f"tracked file is near/above GitHub 100 MB limit: {normalized} ({size / 1024 / 1024:.1f} MB)"
            )
        elif size >= 25 * 1024 * 1024:
            warnings.append(
                f"large tracked file: {normalized} ({size / 1024 / 1024:.1f} MB)"
            )

    if ".env" in tracked_lower:
        errors.append(".env is tracked; remove it from Git history/index before pushing")


def check_python(errors: list[str], warnings: list[str]) -> None:
    if sys.version_info[:2] != (3, 12):
        warnings.append(
            f"running Python {sys.version_info.major}.{sys.version_info.minor}; project target is Python 3.12.10"
        )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    check_python(errors, warnings)
    check_required_files(errors)
    check_requirements(errors, warnings)
    check_git(errors, warnings)

    print("SatQuery release audit")
    print(f"Project: {PROJECT_ROOT}")

    if warnings:
        print("\nWARNINGS")
        for item in warnings:
            print(f"  - {item}")

    if errors:
        print("\nERRORS")
        for item in errors:
            print(f"  - {item}")
        print(f"\nFAILED: {len(errors)} release-blocking issue(s).")
        return 1

    print("\nPASS: no release-blocking repository/deployment issues detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
