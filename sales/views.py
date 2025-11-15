import pandas as pd
import fitz
import pytesseract
from PIL import Image
import io

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Sale
from .serializers import SaleSerializer
from .utils import parse_sale_with_gemini


class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Sale.objects.filter(user=self.request.user).order_by("-id")

    def create(self, request, *args, **kwargs):
        input_type = request.data.get("input_type")
        request.data['user'] = request.user.id
        if input_type not in ["manual", "pdf", "excel"]:
            return Response({"error": "Invalid input_type"}, status=400)

        # --- Manual ---
        if input_type == "manual":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, 201)

        # --- File inputs ---
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "file is required"}, 400)

        text = self.extract_text(file, input_type)
        structured = parse_sale_with_gemini(text)

        # Normalize missing normalized_name
        for item in structured["items"]:
            item["normalized_name"] = item.get("product_name")

        payload = {
            "user": request.user.id,
            "sale_id": structured["sale_id"],
            "sale_datetime": structured["sale_datetime"],
            "total_amount": structured["total_amount"],
            "source": input_type,
            "raw_receipt_text": text,
            "items": structured["items"],
        }

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, 201)

    # --- Extract text from PDF or Excel ---
    def extract_text(self, file, kind):
        if kind == "pdf":
            return self.read_pdf(file)
        return self.read_excel(file)

    def read_pdf(self, file):
        text = ""
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf:
            txt = page.get_text("text")
            if txt.strip():
                text += txt + "\n"
            else:
                img = Image.open(io.BytesIO(page.get_pixmap(dpi=300).tobytes("png")))
                text += pytesseract.image_to_string(img)
        return text.strip()

    def read_excel(self, file):
        df = pd.read_excel(file)
        return df.to_string()