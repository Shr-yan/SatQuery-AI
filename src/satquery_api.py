from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
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

from satquery_service import (
    execute_query,
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


app = FastAPI(
    title="SatQuery AI API",
    description=(
        "Natural-language Sentinel-2 "
        "satellite analysis service."
    ),
    version="0.2.0",
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


@app.get("/")
def root():

    return {
        "name": "SatQuery AI",
        "status": "running",
        "version": "0.2.0",
        "web_app": "/app",
        "documentation": "/docs",
        "supported_analysis": [
            "NDVI",
            "vegetation",
        ],
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


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
                "type": (
                    error["type"]
                ),

                "message": (
                    error["message"]
                ),
            },
        )

    return response


@app.get("/result-image")
def result_image(
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