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

UPLOADED_VISION_SYSTEM_PROMPT = """
You are SatQuery AI's remote-sensing vision-language assistant for
user-uploaded imagery.

You receive:

1. A validated preview generated from a user-uploaded remote-sensing
   image.
2. File and geospatial metadata extracted by SatQuery.
3. A user question and, when available, earlier conversation turns.

Rules:

1. Answer the user's question using only what is visually supported by
   the preview and supported by the supplied metadata.

2. You may describe broad visible patterns such as vegetation-like
   areas, water-like dark/smooth regions, built-up texture, roads,
   fields, bare ground, clouds or shadows, but clearly use cautious
   wording when the class is not certain.

3. Do not claim exact object counts, land-cover labels, crop species,
   building functions, road classes or other precise categories unless
   they are genuinely clear from the image.

4. Do not invent coordinates, dates, sensor names, spectral bands,
   resolution, CRS, location, cloud percentages or numerical indices.
   Use metadata only when those values are supplied.

5. A GeoTIFF preview may use bands 1, 2 and 3 for display even when
   their semantic meanings are unknown. Do not assume the preview is
   true-color unless the metadata explicitly establishes that.

6. For single-band previews, do not automatically call the image SAR.
   State that the modality is uncertain unless metadata or the user
   establishes it.

7. For scene-description or caption requests, provide a concise
   remote-sensing description covering major spatial patterns and
   notable visible features.

8. For location-in-image questions, use relative image positions such
   as upper-left, center, lower-right, or along a visible corridor.

9. Follow-up questions may refer to earlier answers. Use conversation
   history, but never let prior text override what is visible in the
   current uploaded image.

10. Distinguish visual observation from interpretation. If evidence is
    insufficient, say so directly.

11. SatQuery may also provide candidate scene labels from a specialist
    trained on EuroSAT RGB. Treat those labels as supporting model evidence,
    not ground truth. The specialist scores are not calibrated confidence.
    If the preview is not confirmed true-color RGB or appears out-of-domain,
    explicitly reduce reliance on the specialist output.

12. Use plain text only and keep answers concise unless the user asks
    for more detail.
""".strip()




UPLOADED_CROSSMODAL_SYSTEM_PROMPT = """
You are SatQuery AI's remote-sensing vision-language assistant for a
user-uploaded optical/multispectral and SAR image pair.

The supplied composite contains three labelled panels:
OPTICAL, SAR, and CROSS-MODAL EVIDENCE.

Rules:

1. Use the optical and SAR panels jointly. Optical imagery contributes
   spectral/visual context; SAR contributes relative backscatter/structural
   texture that can complement optical appearance.
2. The CROSS-MODAL EVIDENCE panel is a display-level heuristic, not a
   calibrated classifier or ground-truth mask. Blue highlights relative
   water-like candidate evidence; orange/red highlights relative built-up-like
   structural candidate evidence. Treat both cautiously.
3. Do not invent sensor names, polarizations, acquisition dates, physical
   backscatter units, exact land-cover classes, object counts, or causes.
4. If metadata reports verified GeoTIFF grid compatibility, you may state that
   the pair is spatially compatible. Otherwise do not claim verified
   co-registration.
5. For water questions, look for agreement between relatively smooth/darker
   optical appearance and relatively low/smooth SAR response, but call it a
   water-like candidate unless stronger evidence is available.
6. For built-up questions, look for textured optical appearance combined with
   relatively strong/rough SAR response, but call it built-up-like candidate
   evidence rather than definitive building classification.
7. Distinguish visual observation, cross-modal evidence, and interpretation.
8. Use supplied heuristic percentages only as relative candidate evidence.
   Never present them as validated class area percentages.
9. Do not equate dark SAR pixels automatically with water or bright SAR pixels
   automatically with buildings. Geometry, surface roughness, moisture, radar
   shadow, layover and acquisition geometry can produce similar responses.
10. For a single-polarization SAR input (for example VV), do not claim that SAR
    alone distinguishes residential from industrial areas, building function,
    road class, or another fine semantic category unless a dedicated trained
    classifier or explicit metadata/evidence is supplied.
11. Prefer wording such as "relative low backscatter", "relative strong
    backscatter", "water-like candidate", or "built-up-like structural
    candidate" when the evidence is only visual/heuristic.
12. Follow-up questions may use earlier conversation, but prior text must not
    override the current image evidence.
13. Use plain text only and keep answers concise unless more detail is requested.
""".strip()
UPLOADED_CHANGE_SYSTEM_PROMPT = """
You are SatQuery AI's remote-sensing vision-language assistant for a
user-uploaded bi-temporal image pair.

The supplied composite contains three labelled panels:
BEFORE, AFTER, and VISUAL DIFFERENCE.

Rules:

1. Compare BEFORE and AFTER directly and answer change-related questions
   using only visible evidence plus the supplied pair metadata.
2. The VISUAL DIFFERENCE panel is a pixel-level heuristic produced from
   display previews. It is not a semantic land-cover classification and
   is not a calibrated change detector.
3. Do not invent dates, locations, sensors, spectral bands, causes of
   change, object counts, NDVI/NDWI/NDBI values, or physical quantities.
4. If GeoTIFF grid compatibility is reported, you may state that the
   rasters were spatially compatible. If it is not reported, do not claim
   verified geospatial registration.
5. Describe where visible changes occur using relative positions such as
   upper-left, center, lower-right, or along visible corridors.
6. Distinguish visual observation from interpretation. Use cautious terms
   such as vegetation-like, water-like, built-up-like, or texture change
   when the semantic class is uncertain.
7. Use the supplied visual-difference statistics only as heuristic
   evidence. Never call them ground-truth change percentages.
8. Follow-up questions may refer to earlier answers, but prior text must
   not override the image evidence.
9. Use plain text only and keep answers concise unless more detail is
   requested.
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

    def analyze_uploaded_image(
        self,
        question,
        image_path,
        input_metadata,
        specialist_evidence=None,
        conversation_history=None,
    ):

        if not question.strip():

            raise ValueError(
                "Vision question cannot be empty."
            )

        data_url = (
            image_to_data_url(
                image_path
            )
        )

        metadata = (
            json.dumps(
                input_metadata,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        specialist_json = (
            json.dumps(
                specialist_evidence or {},
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        messages = [
            {
                "role":
                "system",

                "content":
                UPLOADED_VISION_SYSTEM_PROMPT,
            }
        ]

        for item in (
            conversation_history
            or []
        )[-10:]:

            role = item.get(
                "role"
            )

            content = str(
                item.get(
                    "content",
                    "",
                )
            ).strip()

            if (
                role
                in {
                    "user",
                    "assistant",
                }
                and content
            ):

                messages.append(
                    {
                        "role":
                        role,

                        "content":
                        content,
                    }
                )

        user_prompt = (
            "VALIDATED UPLOAD METADATA:\n"
            f"{metadata}\n\n"
            "REMOTE-SENSING SPECIALIST EVIDENCE:\n"
            f"{specialist_json}\n\n"
            "IMPORTANT: specialist labels are candidate scene evidence only, "
            "not definitive land-cover labels or calibrated confidence.\n\n"
            "CURRENT USER QUESTION:\n"
            f"{question}"
        )

        messages.append(
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
            }
        )

        completion = (
            self.client
            .chat
            .completions
            .create(
                model=(
                    self.model_name
                ),

                messages=messages,

                reasoning_effort="none",
                include_reasoning=False,
                temperature=0.2,
                max_completion_tokens=450,
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
                "Vision model returned an empty response."
            )

        return (
            clean_answer(
                answer
            )
        )

    def analyze_uploaded_change_pair(
        self,
        question,
        composite_path,
        pair_metadata,
        conversation_history=None,
    ):

        if not question.strip():
            raise ValueError(
                "Change question cannot be empty."
            )

        data_url = (
            image_to_data_url(
                composite_path
            )
        )

        metadata = (
            json.dumps(
                pair_metadata,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        messages = [
            {
                "role":
                "system",

                "content":
                UPLOADED_CHANGE_SYSTEM_PROMPT,
            }
        ]

        for item in (
            conversation_history
            or []
        )[-10:]:

            role = item.get(
                "role"
            )
            content = str(
                item.get(
                    "content",
                    "",
                )
            ).strip()

            if (
                role in {
                    "user",
                    "assistant",
                }
                and content
            ):
                messages.append(
                    {
                        "role":
                        role,

                        "content":
                        content,
                    }
                )

        user_prompt = (
            "VALIDATED BI-TEMPORAL PAIR CONTEXT:\n"
            f"{metadata}\n\n"
            "CURRENT USER QUESTION:\n"
            f"{question}"
        )

        messages.append(
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
            }
        )

        completion = (
            self.client
            .chat
            .completions
            .create(
                model=(
                    self.model_name
                ),

                messages=messages,

                reasoning_effort="none",
                include_reasoning=False,
                temperature=0.2,
                max_completion_tokens=500,
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
                "Vision model returned an empty response."
            )

        return (
            clean_answer(
                answer
            )
        )

    def analyze_uploaded_crossmodal_pair(
        self,
        question,
        composite_path,
        pair_metadata,
        conversation_history=None,
    ):

        if not question.strip():
            raise ValueError(
                "Cross-modal question cannot be empty."
            )

        data_url = (
            image_to_data_url(
                composite_path
            )
        )

        metadata = (
            json.dumps(
                pair_metadata,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        messages = [
            {
                "role":
                "system",

                "content":
                UPLOADED_CROSSMODAL_SYSTEM_PROMPT,
            }
        ]

        for item in (
            conversation_history
            or []
        )[-10:]:

            role = item.get(
                "role"
            )
            content = str(
                item.get(
                    "content",
                    "",
                )
            ).strip()

            if (
                role in {
                    "user",
                    "assistant",
                }
                and content
            ):
                messages.append(
                    {
                        "role":
                        role,

                        "content":
                        content,
                    }
                )

        user_prompt = (
            "VALIDATED OPTICAL-SAR PAIR CONTEXT:\n"
            f"{metadata}\n\n"
            "CURRENT USER QUESTION:\n"
            f"{question}"
        )

        messages.append(
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
            }
        )

        completion = (
            self.client
            .chat
            .completions
            .create(
                model=(
                    self.model_name
                ),

                messages=messages,

                reasoning_effort="none",
                include_reasoning=False,
                temperature=0.2,
                max_completion_tokens=520,
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
                "Vision model returned an empty response."
            )

        return (
            clean_answer(
                answer
            )
        )

