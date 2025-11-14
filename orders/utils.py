import os
import json
import google.generativeai as genai
from datetime import datetime
from difflib import get_close_matches
from inventory.models import Medicine


# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

OrderSchema = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string"},
        "order_datetime": {"type": "string"},
        "total_amount": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "price": {"type": "number"},
                    "amount": {"type": "number"},
                    "confidence": {"type": "number"}   # ⭐ NEW
                },
                "required": ["product_name", "quantity", "price", "amount"]
            }
        }
    },
    "required": ["order_id", "order_datetime", "total_amount", "items"]
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": OrderSchema
    }
)


def parse_invoice_with_gemini(invoice_text: str) -> dict:
    """
    Sends invoice text to Gemini 2.5 with STRICT structured output.
    Works on schema-supported models.
    """

    prompt = f"""
Extract structured order data from this pharmacy invoice text.

{invoice_text}

Follow these rules:
- If order_id missing → generate AUTO-<timestamp>
- If order_datetime missing → use today's ISO date
- Fix OCR spelling mistakes
- For each item, generate a confidence score between 0 and 1
  (1 = certain, 0 = very uncertain)
- ONLY return JSON following the schema
"""

    response = model.generate_content(prompt)

    if hasattr(response, "output") and response.output:
        return response.output

    # fallback to text mode
    raw = response.text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)


def match_medicine_by_name(name: str):
    """
    Fuzzy match the medicine name against DB.
    Handles OCR distortions like:
    - 'Paracetml' → Paracetamol 650mg
    - 'Ascroil' → Ascoril Syrup
    """

    query = name.lower().strip()

    medicines = list(Medicine.objects.all())
    if not medicines:
        return None

    names = [m.name.lower() for m in medicines]

    close = get_close_matches(query, names, n=1, cutoff=0.5)

    if close:
        return Medicine.objects.get(name__iexact=close[0])

    return None