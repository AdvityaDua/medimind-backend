import os
import json
import google.generativeai as genai
from difflib import get_close_matches
from inventory.models import Medicine

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

SaleSchema = {
    "type": "object",
    "properties": {
        "sale_id": {"type": "string"},
        "sale_datetime": {"type": "string"},
        "total_amount": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "price": {"type": "number"},
                    "amount": {"type": "number"}
                },
                "required": ["product_name", "quantity", "price", "amount"]
            }
        }
    },
    "required": ["sale_id", "sale_datetime", "total_amount", "items"]
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": SaleSchema
    }
)

def parse_sale_with_gemini(text):
    prompt = f"""
Extract structured SALE data from this bill.
{text}
ONLY return JSON according to schema.
"""

    response = model.generate_content(prompt)

    if hasattr(response, "output"):
        return response.output

    raw = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)


def match_medicine_by_name(name: str):
    name = name.lower().strip()
    meds = list(Medicine.objects.all())

    if not meds:
        return None

    choices = [m.name.lower() for m in meds]
    close = get_close_matches(name, choices, n=1, cutoff=0.5)

    if close:
        return Medicine.objects.get(name__iexact=close[0])

    return None