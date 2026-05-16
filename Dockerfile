FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el modelo
COPY yolo11x-pose.pt .

COPY . .

RUN mkdir -p uploads reports capturas_riesgo static/frames

EXPOSE 5000

CMD ["python", "web_flask.py"]
