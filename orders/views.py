import os
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
import fitz 
import pytesseract
from PIL import Image
import io
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Order
from .serializers import OrderSerializer
from .utils import parse_invoice_with_gemini



class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            from .serializers import OrderResponseSerializer
            return OrderResponseSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        input_type = request.data.get("input_type")

        if input_type not in ["manual", "pdf", "excel"]:
            return Response({"error": "Invalid input_type"}, status=400)

        if input_type == "manual":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, source="manual")
            return Response(serializer.data, status=201)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "File required"}, status=400)

        extracted_text = self.extract_text_from_file(uploaded_file, input_type)

        structured = parse_invoice_with_gemini(extracted_text)

        items = structured.get("items", [])
        for i in items:
            if "normalized_name" not in i or not i["normalized_name"]:
                i["normalized_name"] = i.get("product_name")

        final_payload = {
            "user": request.user.id,
            "order_id": structured.get("order_id"),
            "order_datetime": structured.get("order_datetime"),
            "total_amount": structured.get("total_amount"),
            "source": input_type,
            "raw_receipt_text": extracted_text,
            "items": items,
            "input_type": "manual"
        }

        serializer = self.get_serializer(data=final_payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

    def extract_text_from_file(self, file, input_type):
        if input_type == "pdf":
            return self.read_pdf(file)
        if input_type == "excel":
            return self.read_excel(file)

    def read_pdf(self, file):
        pdf_bytes = file.read()
        text = ""

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception:
            return ""

        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text += page_text + "\n"
            else:
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                text += pytesseract.image_to_string(img) + "\n"

        return text.strip()

    def read_excel(self, file):
        df = pd.read_excel(file)
        return df.to_string()