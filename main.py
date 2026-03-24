from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import os
import shutil
from pathlib import Path

from excel_parser import parse_excel
from pdf_generator import generate_presentation_pdf

app = FastAPI(title="Generador de Presentaciones - Grupo Grandir")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.post("/api/generate")
async def generate_pdf(request: Request):
    try:
        form = await request.form()

        # Get Excel file
        excel_file = form.get("excelFile")
        if not excel_file:
            raise HTTPException(status_code=400, detail="Falta el archivo Excel")

        excel_path = UPLOAD_DIR / excel_file.filename
        with open(excel_path, "wb") as buffer:
            shutil.copyfileobj(excel_file.file, buffer)

        # Get text fields
        project_title = form.get("project_title", "PROYECTO")
        text_sections = {
            "resumen": form.get("text_resumen", ""),
            "estudio_mercado": form.get("text_estudio", ""),
            "gestor": form.get("text_gestor", ""),
            "riesgos": form.get("text_riesgos", ""),
        }

        # Get photos by category
        image_paths_by_category = {"portada": [], "fachada": [], "interior": []}
        
        for key in form:
            for category in ["portada", "fachada", "interior"]:
                if key.startswith(f"{category}_"):
                    file = form[key]
                    if hasattr(file, 'filename') and file.filename:
                        photo_path = UPLOAD_DIR / file.filename
                        with open(photo_path, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        image_paths_by_category[category].append(str(photo_path))

        # Parse Excel
        financial_data = parse_excel(str(excel_path))

        # Generate PDF
        output_pdf_path = str(OUTPUT_DIR / "Informe_Viabilidad_Generado.pdf")
        generate_presentation_pdf(
            output_pdf_path,
            financial_data,
            image_paths_by_category,
            project_title,
            text_sections
        )

        return FileResponse(
            output_pdf_path,
            media_type="application/pdf",
            filename="Informe_Viabilidad.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
