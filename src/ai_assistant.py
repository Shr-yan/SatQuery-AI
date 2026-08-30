import json
import os

from dotenv import (
    load_dotenv,
)

from groq import (
    Groq,
)

from satquery_service import (
    execute_query,
)


load_dotenv()


MODEL_NAME = (
    "openai/gpt-oss-20b"
)


SYSTEM_PROMPT = """
You are SatQuery AI, an interactive
remote-sensing assistant.

You have two responsibilities:

A. Answer questions from the CURRENT
   SATQUERY ANALYSIS CONTEXT.

B. When the user clearly requests a NEW
   supported satellite analysis, use the
   run_satquery_analysis tool.

SUPPORTED SATQUERY ANALYSES:

- Sentinel-2 RGB imagery
- NDVI / vegetation
- NDWI / water
- NDBI / built-up / urban
- two-date change analysis
- multi-date vegetation trend analysis


GROUNDING RULES:

1. Use only supplied SatQuery measurements
   when answering scientific questions.

2. Never invent NDVI, NDWI, NDBI,
   satellite dates, scene IDs, cloud cover,
   trends, changes or other measurements.

3. If existing context already contains the
   answer, answer directly. Do NOT call the
   analysis tool unnecessarily.

4. If the user explicitly asks for a new
   supported satellite analysis, call
   run_satquery_analysis.

Examples requiring the tool:

"Now analyze water for Varanasi on
2026-02-10."

"Check NDBI for New Delhi on 2026-03-06."

"Compare vegetation in Varanasi between
2026-02-10 and 2026-03-10."

"Show Sentinel-2 imagery for Lucknow on
2026-01-22."


CONTEXT REUSE:

5. You may infer the location from the
   current SatQuery context when the user
   says phrases such as:
   "same place"
   "same location"
   "there"
   "this city"

6. For a SINGLE-DATE current analysis, you
   may reuse its requested date when the
   user's follow-up clearly requests another
   analysis for the same observation/date.

7. For CHANGE or TREND results containing
   multiple dates, do NOT arbitrarily choose
   one date if the user requests a new
   single-date analysis.

   Ask the user which date they want unless
   they explicitly provide one.

8. If the user says "same period", preserve
   the relevant start/end dates where the
   requested SatQuery analysis supports it.

9. The tool query MUST be a complete
   standalone natural-language SatQuery
   query containing all necessary location
   and date information.


SCIENTIFIC RULES:

10. NDVI, NDWI and NDBI are scientific
    remote-sensing indices. They are not
    direct proof of land-cover classes.

11. Positive NDWI/NDBI percentages and
    vegetation labels are heuristic
    indicators.

12. The CNN NDVI estimate is an independent
    learned consistency check. Never call it
    calibrated confidence.

13. Do not claim rainfall, temperature,
    crop type, population, soil moisture or
    other unsupported measurements are
    available unless they are actually
    present in SatQuery context.


ANSWER STYLE:

14. Use plain text only.

15. Do not use Markdown syntax such as
    asterisks, backticks, headings or tables.

16. Do not include long Sentinel-2 scene IDs
    unless the user specifically asks for
    technical scene information.

17. Prefer concise, human-readable answers.

18. Include useful numerical evidence when
    relevant.

19. When reusing a date from the current analysis,
    prefer the user's REQUESTED date, not the selected
    Sentinel-2 acquisition date.

    Example:

    Current context:
    requested date = 2026-02-10
    selected satellite date = 2026-02-08

    Follow-up:
    "Analyze water for the same location and date."

    Tool query must use:
    "Analyze water for Varanasi on 2026-02-10"

    SatQuery itself will decide which satellite
    observation is appropriate.

20. Never replace a user's requested date with a
    selected scene date unless the user explicitly
    asks to analyze that exact acquisition date.
""".strip()


SATQUERY_TOOL = {
    "type":
    "function",

    "function": {

        "name":
        "run_satquery_analysis",

        "description": (
            "Run a new SatQuery Sentinel-2 "
            "analysis. Use this only when "
            "the user requests a new "
            "supported satellite analysis "
            "that cannot be answered from "
            "the current analysis context."
        ),

        "parameters": {

            "type":
            "object",

            "properties": {

                "query": {

                    "type":
                    "string",

                    "description": (
                        "A complete standalone "
                        "SatQuery query containing "
                        "the required analysis, "
                        "location and date or "
                        "date range."
                    ),
                },
            },

            "required": [
                "query"
            ],
        },
    },
}


def clean_answer(
    text,
):

    if not text:

        return ""

    text = (
        text
        .replace(
            "**",
            ""
        )
        .replace(
            "`",
            ""
        )
    )

    return text.strip()


class SatQueryAssistant:

    def __init__(
        self,
        model_name=MODEL_NAME,
    ):

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GROQ_API_KEY was not found. "
                "Check the root .env file."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model_name = (
            model_name
        )


    def build_context(
        self,
        analysis_result,
    ):

        return json.dumps(
            analysis_result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


    def build_messages(
        self,
        question,
        analysis_result,
        conversation_history=None,
    ):

        messages = [
            {
                "role":
                "system",

                "content":
                SYSTEM_PROMPT,
            },

            {
                "role":
                "system",

                "content": (
                    "CURRENT SATQUERY "
                    "ANALYSIS CONTEXT:\n\n"
                    + self.build_context(
                        analysis_result
                    )
                ),
            },
        ]


        if conversation_history:

            for item in (
                conversation_history
            ):

                role = item.get(
                    "role"
                )

                content = item.get(
                    "content"
                )

                if (
                    role
                    not in {
                        "user",
                        "assistant",
                    }
                ):

                    continue

                if not content:

                    continue

                messages.append(
                    {
                        "role":
                        role,

                        "content":
                        str(
                            content
                        ),
                    }
                )


        messages.append(
            {
                "role":
                "user",

                "content":
                question,
            }
        )

        return messages


    def answer(
        self,
        question,
        analysis_result,
        conversation_history=None,
    ):

        if not question.strip():

            raise ValueError(
                "Follow-up question "
                "cannot be empty."
            )


        messages = self.build_messages(
            question=question,

            analysis_result=(
                analysis_result
            ),

            conversation_history=(
                conversation_history
            ),
        )


        first_response = (
            self.client
            .chat
            .completions
            .create(
                model=(
                    self.model_name
                ),

                messages=messages,

                tools=[
                    SATQUERY_TOOL
                ],

                tool_choice="auto",

                temperature=0.1,

                max_completion_tokens=700,

                include_reasoning=False,
            )
        )


        response_message = (
            first_response
            .choices[0]
            .message
        )


        tool_calls = (
            response_message.tool_calls
            or []
        )


        # --------------------------------
        # NO TOOL REQUIRED
        # --------------------------------

        if not tool_calls:

            answer = (
                response_message.content
            )

            if not answer:

                raise RuntimeError(
                    "Groq returned an "
                    "empty response."
                )

            return {
                "answer":
                clean_answer(
                    answer
                ),

                "tool_executed":
                False,

                "tool_query":
                None,

                "analysis_result":
                None,
            }


        # --------------------------------
        # TOOL REQUESTED
        # --------------------------------

        messages.append(
            response_message
        )


        latest_analysis_result = (
            None
        )

        latest_tool_query = (
            None
        )


        for tool_call in tool_calls:

            function_name = (
                tool_call
                .function
                .name
            )


            if (
                function_name
                != "run_satquery_analysis"
            ):

                tool_result = {
                    "success":
                    False,

                    "error": (
                        "Unsupported tool "
                        f"{function_name}"
                    ),
                }

            else:

                try:

                    arguments = (
                        json.loads(
                            tool_call
                            .function
                            .arguments
                        )
                    )

                    tool_query = (
                        arguments.get(
                            "query",
                            ""
                        )
                        .strip()
                    )


                    if not tool_query:

                        raise ValueError(
                            "The SatQuery tool "
                            "received an empty query."
                        )


                    latest_tool_query = (
                        tool_query
                    )


                    print(
                        "\nAI TOOL CALL:"
                    )

                    print(
                        tool_query
                    )


                    tool_result = (
                        execute_query(
                            tool_query
                        )
                    )


                    if tool_result.get(
                        "success"
                    ):

                        latest_analysis_result = (
                            tool_result
                        )


                except Exception as error:

                    tool_result = {
                        "success":
                        False,

                        "error": {
                            "type":
                            "tool_execution_failed",

                            "message":
                            str(
                                error
                            ),
                        },
                    }


            messages.append(
                {
                    "role":
                    "tool",

                    "tool_call_id":
                    tool_call.id,

                    "name":
                    function_name,

                    "content":
                    json.dumps(
                        tool_result,
                        ensure_ascii=False,
                        default=str,
                    ),
                }
            )


        # --------------------------------
        # LET AI EXPLAIN TOOL RESULT
        # --------------------------------

        final_response = (
            self.client
            .chat
            .completions
            .create(
                model=(
                    self.model_name
                ),

                messages=messages,

                tools=[
                    SATQUERY_TOOL
                ],

                tool_choice="none",

                temperature=0.1,

                max_completion_tokens=700,

                include_reasoning=False,
            )
        )


        answer = (
            final_response
            .choices[0]
            .message
            .content
        )


        if not answer:

            answer = (
                "The requested SatQuery "
                "analysis was completed."
            )


        return {
            "answer":
            clean_answer(
                answer
            ),

            "tool_executed":
            (
                latest_analysis_result
                is not None
            ),

            "tool_query":
            latest_tool_query,

            "analysis_result":
            latest_analysis_result,
        }


if __name__ == "__main__":

    assistant = (
        SatQueryAssistant()
    )


    sample_context = {

        "success":
        True,

        "analysis_type":
        "ndvi",

        "change_analysis":
        False,

        "trend_analysis":
        False,

        "location": {
            "requested":
            "Varanasi",

            "resolved":
            "Varanasi, Uttar Pradesh, India",
        },

        "date": {
            "requested":
            "2026-02-10",

            "selected":
            "2026-02-08",
        },

        "vegetation": {
            "mean_ndvi":
            0.1883,
        },
    }


    result = assistant.answer(
        question=(
            "Now analyze water for "
            "the same location and date."
        ),

        analysis_result=(
            sample_context
        ),
    )


    print(
        json.dumps(
            result,
            indent=2,
        )
    )