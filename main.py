"""
FastAPI backend para el generador de informes de viabilidad.
Sirve la UI estática y el endpoint POST /api/generate.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
import traceback
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
    """Recibe Excel + fotos + textos y genera un PDF de viabilidad."""
    try:
        form = await request.form()

        # ── Excel ──
        excel_upload = form.get("excelFile")
        if not excel_upload or not hasattr(excel_upload, 'file'):
            return JSONResponse(
                status_code=400,
                content={"detail": "Falta el archivo Excel"}
            )

        excel_path = UPLOAD_DIR / excel_upload.filename
        content = await excel_upload.read()
        with open(excel_path, "wb") as f:
            f.write(content)

        # ── Texto ──
        project_title = form.get("project_title", "PROYECTO")
        text_sections = {
            "resumen": form.get("text_resumen", "") or "",
            "estudio_mercado": form.get("text_estudio", "") or "",
            "gestor": form.get("text_gestor", "") or "",
            "riesgos": form.get("text_riesgos", "") or "",
        }

        # ── Fotos por categoría ──
        image_paths_by_category = {"portada": [], "fachada": [], "interior": []}

        for key in form:
            for cat in ["portada", "fachada", "interior"]:
                if key.startswith(f"{cat}_"):
                    upload = form[key]
                    if hasattr(upload, 'file') and upload.filename:
                        photo_data = await upload.read()
                        safe_name = f"{cat}_{len(image_paths_by_category[cat])}_{upload.filename}"
                        photo_path = UPLOAD_DIR / safe_name
                        with open(photo_path, "wb") as f:
                            f.write(photo_data)
                        image_paths_by_category[cat].append(str(photo_path))

        # ── Parsear Excel ──
        financial_data = parse_excel(str(excel_path))

        # ── Generar PDF ──
        output_pdf = str(OUTPUT_DIR / "Informe_Viabilidad_Generado.pdf")
        generate_presentation_pdf(
            output_pdf,
            financial_data,
            image_paths_by_category,
            project_title,
            text_sections,
        )

        if not os.path.exists(output_pdf):
            return JSONResponse(
                status_code=500,
                content={"detail": "No se pudo generar el PDF"}
            )

        return FileResponse(
            output_pdf,
            media_type="application/pdf",
            filename=f"Informe_Viabilidad_{project_title.replace(' ', '_')}.pdf",
        )

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error en la generación: {str(e)}"}
        )
