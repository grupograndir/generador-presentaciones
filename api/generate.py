"""
Vercel Serverless Function: /api/generate
Recibe un Excel + fotos por categoría y genera un PDF de viabilidad.
"""

import os
import sys
import shutil
import tempfile
from http.server import BaseHTTPRequestHandler
import cgi
import json
import io

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_parser import parse_excel
from pdf_generator import generate_presentation_pdf


def parse_multipart(handler):
    """Parsea los datos multipart/form-data del request."""
    content_type = handler.headers.get('content-type', '')

    if 'multipart/form-data' not in content_type:
        return {}, {}

    ctype, pdict = cgi.parse_header(content_type)
    if 'boundary' in pdict:
        if isinstance(pdict['boundary'], str):
            pdict['boundary'] = pdict['boundary'].encode('utf-8')

    content_length = int(handler.headers.get('content-length', 0))
    body = handler.rfile.read(content_length)

    environ = {
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': content_type,
        'CONTENT_LENGTH': str(content_length),
    }

    fs = cgi.FieldStorage(
        fp=io.BytesIO(body),
        environ=environ,
        keep_blank_values=True,
    )

    fields = {}
    files = {}

    for key in fs.keys():
        item = fs[key]
        if isinstance(item, list):
            item = item[0]
        if item.filename:
            files[key] = {
                'filename': item.filename,
                'data': item.file.read(),
            }
        else:
            fields[key] = item.value

    return fields, files


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            fields, files = parse_multipart(self)

            if 'excelFile' not in files:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'detail': 'Falta el archivo Excel'}).encode())
                return

            tmp_dir = tempfile.mkdtemp()

            try:
                # Save Excel
                excel_data = files['excelFile']
                excel_path = os.path.join(tmp_dir, excel_data['filename'])
                with open(excel_path, 'wb') as f:
                    f.write(excel_data['data'])

                # Get text fields
                project_title = fields.get('project_title', 'PROYECTO')
                text_sections = {
                    'resumen': fields.get('text_resumen', ''),
                    'estudio_mercado': fields.get('text_estudio', ''),
                    'gestor': fields.get('text_gestor', ''),
                    'riesgos': fields.get('text_riesgos', ''),
                }

                # Save photos by category
                image_paths_by_category = {'portada': [], 'fachada': [], 'interior': []}
                for key, file_data in files.items():
                    for category in ['portada', 'fachada', 'interior']:
                        if key.startswith(f'{category}_'):
                            photo_path = os.path.join(tmp_dir, f"{key}_{file_data['filename']}")
                            with open(photo_path, 'wb') as f:
                                f.write(file_data['data'])
                            image_paths_by_category[category].append(photo_path)

                # Parse Excel
                financial_data = parse_excel(excel_path)

                # Generate PDF
                output_pdf_path = os.path.join(tmp_dir, 'Informe_Viabilidad_Generado.pdf')
                generate_presentation_pdf(
                    output_pdf_path,
                    financial_data,
                    image_paths_by_category,
                    project_title,
                    text_sections
                )

                with open(output_pdf_path, 'rb') as f:
                    pdf_bytes = f.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', 'attachment; filename="Informe_Viabilidad.pdf"')
                self.send_header('Content-Length', str(len(pdf_bytes)))
                self.end_headers()
                self.wfile.write(pdf_bytes)

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'detail': str(e)}).encode())
