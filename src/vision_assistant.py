import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


VISION_MODEL = (
    "qwen/qwen3.6-27b"
)


VISION_SYSTEM_PROMPT = """
You are SatQuery AI's remote-sensing
vision assistant.

You receive:

1. A generated SatQuery satellite or
   analysis image.

2. Structured scientific metadata from
   SatQuery.

3. A user follow-up question.

Rules:

1. Describe only what is visually supported
   by the image and scientifically supported
   by the metadata.

2. Do not invent NDVI, NDWI, NDBI,
   cloud cover, dates, locations, or other
   numerical measurements.

3. Use supplied metadata for exact values.

4. Clearly distinguish:
   - visual observation
   - scientific measurement
   - interpretation

5. Do not claim a land-cover class is
   definitively identified from NDVI, NDWI
   or NDBI alone.

6. For RGB imagery, describe visible spatial
   patterns conservatively.

7. For NDVI, NDWI, NDBI, trend or change
   maps, use the map type and metadata to
   interpret patterns.

8. Do not infer rainfall, crop type,
   population, soil moisture or other
   unsupported variables.

9. Use plain text only.

10. Keep answers concise unless the user
    requests detail.
""".strip()


def clean_answer(
    text,
):

    if not text:

        return ""

    return (
        text
        .replace(
            "**",
            ""
        )
        .replace(
            "`",
            ""
        )
        .strip()
    )


def image_to_data_url(
    image_path,
):

    image_path = Path(
        image_path
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found: "
            f"{image_path}"
        )


    extension = (
        image_path
        .suffix
        .lower()
    )


    mime_types = {
        ".png":
        "image/png",

        ".jpg":
        "image/jpeg",

        ".jpeg":
        "image/jpeg",
    }


    mime_type = (
        mime_types.get(
            extension
        )
    )


    if not mime_type:

        raise ValueError(
            "Vision analysis currently "
            "supports PNG and JPEG images."
        )


    image_bytes = (
        image_path
        .read_bytes()
    )


    encoded = (
        base64.b64encode(
            image_bytes
        )
        .decode(
            "utf-8"
        )
    )


    return (
        f"data:{mime_type};"
        f"base64,{encoded}"
    )


class SatQueryVisionAssistant:

    def __init__(
        self,
        model_name=VISION_MODEL,
    ):

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GROQ_API_KEY was not found."
            )


        self.client = Groq(
            api_key=api_key
        )


        self.model_name = (
            model_name
        )


    def analyze_image(
        self,
        question,
        image_path,
        analysis_result,
        image_type,
    ):

        if not question.strip():

            raise ValueError(
                "Vision question "
                "cannot be empty."
            )


        data_url = (
            image_to_data_url(
                image_path
            )
        )


        metadata = (
            json.dumps(
                analysis_result,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )


        user_prompt = (
            "IMAGE TYPE:\n"
            f"{image_type}\n\n"

            "SATQUERY SCIENTIFIC CONTEXT:\n"
            f"{metadata}\n\n"

            "USER QUESTION:\n"
            f"{question}"
        )


        completion = (
            self.client
            .chat
            .completions
            .create(
                model=(
                    self.model_name
                ),

                messages=[
                    {
                        "role":
                        "system",

                        "content":
                        VISION_SYSTEM_PROMPT,
                    },

                    {
                        "role":
                        "user",

                        "content": [
                            {
                                "type":
                                "text",

                                "text":
                                user_prompt,
                            },

                            {
                                "type":
                                "image_url",

                                "image_url": {
                                    "url":
                                    data_url
                                },
                            },
                        ],
                    },
                ],

                reasoning_effort="none",
                include_reasoning=False,
                temperature=0.2,
                max_completion_tokens=400,
            )
        )


        answer = (
            completion
            .choices[0]
            .message
            .content
        )


        if not answer:

            raise RuntimeError(
                "Vision model returned "
                "an empty response."
            )


        return (
            clean_answer(
                answer
            )
        )