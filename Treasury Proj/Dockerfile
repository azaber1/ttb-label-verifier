FROM python:3.11-slim

# Install Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements first
COPY backend/requirements.txt requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of backend files
COPY backend/app.py app.py

EXPOSE 5001

CMD ["python", "app.py"]
