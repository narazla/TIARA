FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        ffmpeg \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavutil-dev \
        libavfilter-dev \
        libswscale-dev \
        libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
# torch versi CPU dulu agar tidak menarik paket CUDA yang besar
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Unduh model saat build supaya request pertama tidak menunggu unduhan
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')" \
    && python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

COPY . .

CMD ["sh", "-c", "alembic upgrade head && python -m app.scripts.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
