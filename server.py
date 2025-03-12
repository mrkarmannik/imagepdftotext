from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil
import os
import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import magic  # Для определения типа файла
from docling.document_converter import DocumentConverter

# Настройка логирования
logging.basicConfig(filename="/home/appuser/server.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="My API",
    description="API для обработки различных форматов файлов и извлечения текста",
    version="1.0.0",
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Функция для извлечения текста из PDF
def extract_text_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    content = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        if text.strip():
            content.append(text)

        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            image_text = pytesseract.image_to_string(image, lang='rus')
            if image_text.strip():
                content.append(image_text)

    return "\n\n".join(content)

# Функция для извлечения текста из текстовых файлов
def extract_text_from_text_file(file_path):
    converter = DocumentConverter()
    doc = converter.convert(file_path)
    return doc.document.export_to_text()

# Функция для распознавания текста на изображениях
def ocr_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image, lang='rus')

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Сохранение файла
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Определение типа файла
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)

        if file_type == "application/pdf":
            # Обработка PDF
            combined_text = extract_text_from_pdf(file_path)
        elif file_type.startswith("text/") or file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # Обработка текстовых файлов
            combined_text = extract_text_from_text_file(file_path)
        elif file_type.startswith("image/"):
            # Обработка изображений
            combined_text = ocr_image(file_path)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")

        if not combined_text.strip():
            raise ValueError("Текст не распознан")

        logging.info(f"Файл {file.filename} обработан успешно.")
        return {"filename": file.filename, "text": combined_text}

    except Exception as e:
        logging.error(f"Ошибка обработки {file.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Ошибка обработки файла: {str(e)}")

    finally:
        os.remove(file_path)  # Удаляем файл после обработки
