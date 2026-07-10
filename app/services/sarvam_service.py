import json
import requests
from typing import Type, TypeVar
from fastapi import HTTPException
from pydantic import BaseModel
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class SarvamService:
    """
    Service for interacting with the Sarvam AI API.
    Provides structured JSON generation matching Pydantic schemas.
    """

    @staticmethod
    def _get_api_key() -> str:
        """Return the Sarvam API key, raising 400 if key is missing."""
        if not settings.SARVAM_API_KEY:
            raise HTTPException(
                status_code=400,
                detail="SARVAM_API_KEY is not set. Please add it to your .env file."
            )
        return settings.SARVAM_API_KEY

    @classmethod
    def generate_structured_data(
        cls,
        prompt: str,
        schema: Type[T],
        system_instruction: str = None,
        model_name: str = None
    ) -> T:
        """
        Generates structured JSON content via Sarvam and validates it
        against the given Pydantic schema.
        """
        model = model_name or settings.SARVAM_MODEL or "sarvam-105b"
        api_key = cls._get_api_key()

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        brevity_instruction = (
            "\n\nIMPORTANT BREVITY REQUIREMENT:\n"
            "To prevent response truncation, you must be extremely concise. Keep all text descriptions, summaries, "
            "and rationales short and straight to the point. Limit lists (such as acceptance criteria or "
            "recommendations) to at most 3 items. Limit the total number of generated items (like sprint "
            "tickets, theme clusters, or architectural impacts) to a maximum of 4 key items."
        )
        refined_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You MUST respond with a single valid JSON object that strictly "
            f"adheres to the following JSON Schema. Do NOT include any explanation, markdown "
            f"code fences, or extra text — output raw JSON only:\n\n"
            f"{schema_json}\n\n"
            f"{brevity_instruction}"
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": refined_prompt})

        url = "https://api.sarvam.ai/v1/chat/completions"
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300.0)

            if response.status_code != 200:
                print(f"Sarvam API error: status {response.status_code}, response: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Sarvam API returned an error: {response.text}"
                )

            res_json = response.json()
            raw_text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            if not raw_text:
                raise HTTPException(
                    status_code=502,
                    detail="Empty response received from the Sarvam API."
                )

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
                print(f"Sarvam validation failed for {schema.__name__}. Raw:\n{raw_text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Sarvam returned JSON that failed schema validation: {val_err}"
                )

        except HTTPException:
            raise
        except Exception as e:
            print(f"Unexpected Sarvam error: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to query Sarvam API: {str(e)}"
            )

    @classmethod
    def test_connection(cls) -> bool:
        """Quick connectivity test — returns True if Sarvam responds successfully."""
        try:
            api_key = cls._get_api_key()
            url = "https://api.sarvam.ai/v1/chat/completions"
            headers = {
                "api-subscription-key": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "model": settings.SARVAM_MODEL or "sarvam-105b",
                "messages": [{"role": "user", "content": "Ping"}],
                "max_tokens": 10
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Sarvam connection check failed: {e}")
            return False
