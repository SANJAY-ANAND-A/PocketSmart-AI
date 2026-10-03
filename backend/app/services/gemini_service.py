import json
import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.models.product import Product
from app.schemas.recommendation import GeminiStructuredResponse

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Official Google GenAI SDK integration for PocketSmart AI.
    Handles semantic preference understanding, candidate selection, and structured JSON output.
    Never performs authoritative financial arithmetic.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name if model_name is not None else settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

    def is_available(self) -> bool:
        """Checks if the Gemini API key is configured and non-empty."""
        return bool(self.api_key and self.api_key.strip())

    def _get_client(self) -> genai.Client:
        """Lazy initialization of the official Google GenAI client."""
        if self._client is None:
            if not self.is_available():
                raise ValueError("GEMINI_API_KEY is not configured.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def build_prompt(
        self,
        module: str,
        budget: float,
        preferences: str,
        candidates: List[Product],
        has_image: bool = False,
    ) -> str:
        """Constructs a disciplined system prompt with available catalog candidate items."""
        candidate_summary = []
        for p in candidates:
            category_name = None
            try:
                if getattr(p, "category", None) is not None:
                    category_name = p.category.name
            except Exception:
                pass
            if not category_name:
                category_name = p.subcategory or "General"

            candidate_summary.append({
                "id": p.id,
                "name": p.name,
                "category": category_name,
                "price_inr": p.price,
                "platform": p.platform,
                "style": p.style,
                "tags": p.tags,
                "rating": p.rating,
            })

        candidates_json = json.dumps(candidate_summary, indent=2)

        image_instruction = ""
        if has_image:
            image_instruction = """
8. OUTFIT IMAGE ANALYSIS & STRICT PRIVACY RULE:
- An image of the user's outfit has been provided.
- Analyze ONLY garment characteristics: fabric, dominant colors, neckline, styling, and formality to recommend complementary jewelry pieces.
- ABSOLUTE PRIVACY DIRECTIVE: DO NOT identify or describe human faces, person identity, demographics, or biometric traits. No personal identification is allowed."""

        prompt = f"""You are the lead AI Budget Advisor for PocketSmart AI.
The user is planning a budget for the '{module}' module with a total budget limit of ₹{budget:.2f} INR.
User's preferences and requirements:
"{preferences}"

AVAILABLE CANDIDATE CATALOG PRODUCTS:
{candidates_json}

CRITICAL RULES:
1. Recommend 1 to 6 items strictly from the AVAILABLE CANDIDATE CATALOG PRODUCTS list above.
2. You MUST use the exact numerical 'id' for each recommended product. NEVER invent product IDs, product names, or platforms.
3. Recommend reasonable integer quantities (typically 1, or more for small accessories).
4. Aim for the combined estimated total to stay within or reasonably close to ₹{budget:.2f} INR.
5. Provide a short, persuasive explanation for each item describing why it matches the user's style, preferences, and budget.
6. The authoritative price calculation will be performed by the backend engine, not by you.
7. Return strictly valid JSON matching this schema:
{{
  "module": "{module}",
  "summary": "A 1-2 sentence personalized overview of this plan",
  "budget_guidance": "A short strategic advice tip for this budget",
  "preferences": {{
    "style": "Interpreted design style",
    "priority": "Interpreted primary priority",
    "key_aspects": ["keyword1", "keyword2"]
  }},
  "recommendations": [
    {{
      "product_id": 1,
      "quantity": 1,
      "reason": "Detailed justification"
    }}
  ],
  "warnings": []
}}{image_instruction}
"""
        return prompt

    def generate_recommendations(
        self,
        module: str,
        budget: float,
        preferences: str,
        candidates: List[Product],
        image_bytes: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> Optional[GeminiStructuredResponse]:
        """
        Calls Gemini with the candidate catalog and parses the structured JSON response.
        Supports optional multimodal outfit image for jewelry styling.
        Returns GeminiStructuredResponse on success, or None on any failure/timeout
        to gracefully trigger the deterministic fallback engine.
        """
        if not self.is_available():
            logger.info("Gemini API key is not configured; using deterministic fallback.")
            return None

        if not candidates:
            logger.warning("No candidate catalog products provided to Gemini.")
            return None

        has_image = bool(image_bytes and image_mime_type)
        prompt = self.build_prompt(module, budget, preferences, candidates, has_image=has_image)

        try:
            client = self._get_client()
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,  # Low temperature for deterministic adherence to catalog
            )

            contents: Any = prompt
            if has_image:
                contents = [
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type),
                ]

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )


            raw_text = response.text
            if not raw_text or not raw_text.strip():
                logger.warning("Gemini returned empty response text.")
                return None

            # Parse JSON
            data = json.loads(raw_text)

            # Validate with Pydantic
            structured_output = GeminiStructuredResponse.model_validate(data)
            return structured_output

        except json.JSONDecodeError as jde:
            logger.warning(f"Failed to decode Gemini JSON response: {jde}")
            return None
        except Exception as e:
            logger.warning(f"Gemini API request failed: {e}")
            return None


gemini_service = GeminiService()
