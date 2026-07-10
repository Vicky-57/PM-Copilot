import json
import requests
from typing import Type, TypeVar
from fastapi import HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from app.config import settings

T = TypeVar("T", bound=BaseModel)

# Lazy import to avoid circular dependency
def _get_sarvam_service():
    from app.services.sarvam_service import SarvamService
    return SarvamService

class GeminiService:
    @staticmethod
    def _get_gemini_client():
        """Configure the Gemini client, throwing error if API key is missing."""
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=400,
                detail="GEMINI_API_KEY is not set. Please set the GEMINI_API_KEY in your .env file or environment variables."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)

    @classmethod
    def generate_structured_data(
        cls, 
        prompt: str, 
        schema: Type[T], 
        system_instruction: str = None,
        model_name: str = "gemini-2.5-flash"
    ) -> T:
        """
        Generates content from the LLM provider and forces a structured JSON response matching the Pydantic schema.
        Provider priority: Sarvam > Groq > Gemini. Falls back to next provider on error.
        """
        # 1. Try Sarvam first (highest priority)
        if settings.SARVAM_API_KEY:
            try:
                SarvamService = _get_sarvam_service()
                # Don't pass Gemini-specific model names to Sarvam — let it use its default
                sarvam_model = None if (model_name and model_name.startswith("gemini")) else model_name
                return SarvamService.generate_structured_data(prompt, schema, system_instruction, sarvam_model)
            except HTTPException:
                # Re-raise Sarvam's own HTTP errors — don't silently fall back, so the real error is visible
                raise
            except Exception as e:
                print(f"[SarvamService] Non-HTTP error, attempting fallback: {type(e).__name__}: {e}")
                # Fall through to Groq or Gemini only for network/unexpected errors
                if not settings.GROQ_API_KEY and not settings.GEMINI_API_KEY:
                    raise e

        # 2. Try Groq
        if settings.GROQ_API_KEY:
            try:
                return cls._generate_via_groq(prompt, schema, system_instruction)
            except Exception as e:
                print(f"Groq API call encountered an error: {e}.")
                if settings.GEMINI_API_KEY:
                    print("Falling back to Gemini API for this request...")
                    return cls._generate_via_gemini(prompt, schema, system_instruction, model_name)
                else:
                    raise e

        # 3. Fall back to Gemini
        return cls._generate_via_gemini(prompt, schema, system_instruction, model_name)

    @classmethod
    def _generate_via_groq(
        cls,
        prompt: str,
        schema: Type[T],
        system_instruction: str = None
    ) -> T:
        """Helper to invoke Groq API and parse response matching Pydantic schema."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        refined_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You MUST return a JSON object that strictly adheres to the following JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Ensure all required fields are filled and contain correct types."
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": refined_prompt})

        is_xai = settings.GROQ_API_KEY.startswith("xai-")
        model = "grok-beta" if (is_xai and ("llama" in settings.GROQ_MODEL or "mixtral" in settings.GROQ_MODEL)) else (settings.GROQ_MODEL or "llama-3.3-70b-versatile")
        api_url = "https://api.x.ai/v1/chat/completions" if is_xai else "https://api.groq.com/openai/v1/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 4096
        }


        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Groq API returned an error: {response.text}"
                )
                
            res_json = response.json()
            choice = res_json.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "").strip()
            
            if not content:
                raise HTTPException(
                    status_code=502,
                    detail="Empty response received from the Groq API."
                )

            # Clean markdown JSON wrapping if present
            if content.startswith("```json"):
                content = content.split("```json", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            content = content.strip()

            # Parse and validate JSON
            validated_data = schema.model_validate_json(content)
            return validated_data

        except json.JSONDecodeError as jde:
            print(f"Failed to parse JSON response from Groq. Raw content:\n{content}")
            raise HTTPException(
                status_code=502,
                detail=f"Groq returned an invalid JSON response: {jde}."
            )
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to query Groq API: {str(e)}"
            )

    @classmethod
    def _generate_via_gemini(
        cls,
        prompt: str,
        schema: Type[T],
        system_instruction: str = None,
        model_name: str = "gemini-2.5-flash"
    ) -> T:
        """Helper to invoke Gemini API and parse response matching Pydantic schema."""
        cls._get_gemini_client()
        
        try:
            # Bypass response_schema for large/complex models to prevent alphabetical token limits/EOF truncation
            bypass_schema = schema.__name__ in ("PRDGenerationResponse", "SprintPlanResponse", "FeasibilityResponse")
            config = genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=None if bypass_schema else schema,
                temperature=0.2,
                max_output_tokens=8192
            )
        except Exception as config_err:
            print(f"GenerationConfig schema generation failed: {config_err}")
            config = genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2,
                max_output_tokens=8192
            )
            
        refined_prompt = prompt
        if not hasattr(config, "response_schema") or config.response_schema is None:
            schema_json = json.dumps(schema.model_json_schema(), indent=2)
            refined_prompt = (
                f"{prompt}\n\n"
                f"IMPORTANT: You MUST return a JSON object that strictly adheres to the following JSON Schema:\n"
                f"```json\n{schema_json}\n```\n"
                f"Ensure all required fields are filled and contain correct types."
            )

        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            
            response = model.generate_content(
                refined_prompt,
                generation_config=config
            )
            
            if not response.text:
                raise HTTPException(
                    status_code=502,
                    detail="Empty response received from the Gemini API."
                )
            
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()
            
            try:
                validated_data = schema.model_validate_json(response_text)
                return validated_data
            except Exception as validation_err:
                print(f"Pydantic validation failed for schema {schema.__name__}. Raw response text was:\n{response_text}")
                raise validation_err
            
        except json.JSONDecodeError as jde:
            print(f"Failed to parse Gemini JSON. Raw response:\n{response.text}")
            raise HTTPException(
                status_code=502,
                detail=f"Gemini returned an invalid JSON response: {jde}."
            )
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to query Gemini API: {str(e)}"
            )
        
    @classmethod
    def test_connection(cls) -> bool:
        """Helper to quickly test if the API key and connection are working. Checks Sarvam > Groq > Gemini."""
        # 1. Try Sarvam
        if settings.SARVAM_API_KEY:
            try:
                SarvamService = _get_sarvam_service()
                return SarvamService.test_connection()
            except Exception as e:
                print(f"Sarvam connection check failed: {e}")
                return False

        # 2. Try Groq
        elif settings.GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                is_xai = settings.GROQ_API_KEY.startswith("xai-")
                model = "grok-beta" if (is_xai and ("llama" in settings.GROQ_MODEL or "mixtral" in settings.GROQ_MODEL)) else (settings.GROQ_MODEL or "llama-3.1-70b-versatile")
                api_url = "https://api.x.ai/v1/chat/completions" if is_xai else "https://api.groq.com/openai/v1/chat/completions"
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "Ping"}],
                    "max_tokens": 10
                }
                response = requests.post(api_url, headers=headers, json=payload, timeout=10)
                return response.status_code == 200
            except Exception as e:
                print(f"Groq connection check failed: {e}")
                return False

        # 3. Try Gemini
        else:
            try:
                cls._get_gemini_client()
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content("Ping")
                return bool(response.text)
            except Exception as e:
                print(f"Gemini connection check failed: {e}")
                return False

