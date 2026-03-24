from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import shutil
from pathlib import Path

from excel_parser import parse_excel
from pdf_generator import generate_presentation_pdf

app = FastAPI(title="Generador de Presentaciones - Palomar/Almenara")

# Directorio base para subir archivos temporalmente
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Mount carpetas estáticas (Frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/api/generate")
async def generate_pdf(
    excelFile: UploadFile = File(...),
    photo1: Optional[UploadFile] = File(None),
    photo2: Optional[UploadFile] = File(None),
    photo3: Optional[UploadFile] = File(None),
    project_title: str = Form("PROYECTO PALOMAR / ALMENARA"),
    gestor_name: str = Form("[NOMBRE DEL GESTOR]"),
    project_description: str = Form(""),
):
    try:
        # Save Excel file
        excel_path = UPLOAD_DIR / excelFile.filename
        with open(excel_path, "wb") as buffer:
            shutil.copyfileobj(excelFile.file, buffer)
        
        # Save images if provided
        image_paths = []
        for photo in [photo1, photo2, photo3]:
            if photo and photo.filename:
                photo_path = UPLOAD_DIR / photo.filename
                with open(photo_path, "wb") as buffer:
                    shutil.copyfileobj(photo.file, buffer)
                image_paths.append(str(photo_path))

        # Parse Excel
        financial_data = parse_excel(str(excel_path))

        # Generate PDF
        output_pdf_path = str(OUTPUT_DIR / "Informe_Viabilidad_Generado.pdf")
        generate_presentation_pdf(
            output_pdf_path, 
            financial_data, 
            image_paths, 
            project_title, 
            gestor_name, 
            project_description
        )

        return FileResponse(
            output_pdf_path, 
            media_type="application/pdf", 
            filename="Informe_Viabilidad.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
