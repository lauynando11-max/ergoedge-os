cat > ~/ergoedge-os/Dockerfile << 'EOF'
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el modelo (clave)
COPY yolo11x-pose.pt .

COPY . .

RUN mkdir -p uploads reports capturas_riesgo static/frames

EXPOSE 5000

CMD ["python", "web_flask.py"]
EOF
