cat > ~/ergoedge-os/Dockerfile << 'EOF'
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el modelo
COPY yolo11x-pose.pt .

COPY . .

RUN mkdir -p uploads reports capturas_riesgo static/frames

EXPOSE 5000

# Usar Gunicorn en lugar de Flask directamente
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_flask:app"]
EOF
