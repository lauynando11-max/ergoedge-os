FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Descargar el modelo YOLO durante el build
RUN python -c "from ultralytics import YOLO; model = YOLO('yolo11n-pose.pt')"

COPY . .

RUN mkdir -p uploads reports capturas_riesgo static/frames

EXPOSE 5000

CMD ["python", "web_flask.py"]
