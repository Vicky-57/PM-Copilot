import json
from typing import Type, TypeVar
from fastapi import HTTPException
from pydantic import BaseModel
import anthropic
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class ClaudeService:
    """
    Service for interacting with the Anthropic Claude API.
    Provides structured JSON generation matching Pydantic schemas.
    """

    @staticmethod
    def _get_client() -> anthropic.Anthropic:
        """Return a configured Anthropic client, raising 400 if key is missing."""
        if not settings.CLAUDE_API_KEY:
            raise HTTPException(
                status_code=400,
                detail="CLAUDE_API_KEY is not set. Please add it to your .env file."
            )
        return anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY, timeout=300.0)

    @classmethod
    def generate_structured_data(
        cls,
        prompt: str,
        schema: Type[T],
        system_instruction: str = None,
        model_name: str = None
    ) -> T:
        """
        Generates structured JSON content via Claude and validates it
        against the given Pydantic schema.
        """
        model = model_name or settings.CLAUDE_MODEL or "claude-sonnet-4-5-20250929"
        client = cls._get_client()

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        refined_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You MUST respond with a single valid JSON object that strictly "
            f"adheres to the following JSON Schema. Do NOT include any explanation, markdown "
            f"code fences, or extra text — output raw JSON only:\n\n"
            f"{schema_json}"
        )

        messages = [{"role": "user", "content": refined_prompt}]

        system_parts = []
        if system_instruction:
            system_parts.append(system_instruction)
        system_parts.append(
            "You are a highly accurate structured data generator. "
            "Always respond with raw JSON matching the schema exactly. "
            "No markdown, no code fences, no explanations."
        )
        system_text = "\n\n".join(system_parts)

        try:
            response = client.messages.create(
                model=model,
                max_tokens=16384,
                system=system_text,
                messages=messages,
                temperature=0.2
            )

            raw_text = response.content[0].text.strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1]
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()

            try:
                validated = schema.model_validate_json(raw_text)
                return validated
            except Exception as val_err:
                print(f"Claude validation failed for {schema.__name__}. Raw:\n{raw_text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Claude returned JSON that failed schema validation: {val_err}"
                )

        except anthropic.APIStatusError as api_err:
            print(f"Claude API error: {api_err}")
            raise HTTPException(
                status_code=api_err.status_code,
                detail=f"Claude API error: {api_err.message}"
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Unexpected Claude error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to query Claude API: {str(e)}"
            )

    @classmethod
    def test_connection(cls) -> bool:
        """Quick connectivity test — returns True if Claude responds successfully."""
        try:
            client = cls._get_client()
            response = client.messages.create(
                model=settings.CLAUDE_MODEL or "claude-sonnet-4-5-20250929",
                max_tokens=10,
                messages=[{"role": "user", "content": "Ping"}]
            )
            return bool(response.content)
        except Exception as e:
            print(f"Claude connection check failed: {e}")
            return False
