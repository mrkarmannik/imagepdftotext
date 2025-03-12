FROM python:3.10-slim

WORKDIR /app

# Устанавливаем зависимости для Tesseract OCR и libmagic
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    libtesseract-dev \
    libleptonica-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя appuser
RUN useradd -m appuser

# Изменяем права доступа к директории /app
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Переключаемся на пользователя appuser
USER appuser

# Добавляем путь для локально установленных пакетов
ENV PATH="/home/appuser/.local/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages --user -r requirements.txt

COPY . ./

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

