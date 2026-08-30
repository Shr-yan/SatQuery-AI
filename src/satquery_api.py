from pathlib import Path
from typing import Any

from fastapi.staticfiles import (
    StaticFiles,
)

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
        "satellite imagery, scientific "
        "analysis and grounded AI "
        "follow-up assistant."
    ),
    version="0.4.0",
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


@app.get("/")
def root():

    return {
        "name":
        "SatQuery AI",

        "status":
        "running",

        "version":
        "0.4.0",

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
        ],
    }


@app.get("/health")
def health():

    return {
        "status":
        "healthy",

        "version":
        "0.4.0",
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