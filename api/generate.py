"""
Vercel Serverless Function: POST /api/generate
Recibe Excel + fotos por categoría + textos y genera un PDF de viabilidad.
"""

import os
import sys
import shutil
import tempfile
import json
import io
import cgi
import traceback
from http.server import BaseHTTPRequestHandler

# Añadir el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_parser import parse_excel
from pdf_generator import generate_presentation_pdf


def _parse_multipart(handler):
    """Parsea multipart/form-data y devuelve (fields, files)."""
    content_type = handler.headers.get('content-type', '')
    if 'multipart/form-data' not in content_type:
        return {}, {}

    ctype, pdict = cgi.parse_header(content_type)
    if 'boundary' in pdict:
        if isinstance(pdict['boundary'], str):
            pdict['boundary'] = pdict['boundary'].encode('utf-8')

    content_length = int(handler.headers.get('content-length', 0))
    body = handler.rfile.read(content_length)

    fs = cgi.FieldStorage(
        fp=io.BytesIO(body),
        environ={
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': str(content_length),
        },
        keep_blank_values=True,
    )

    fields = {}
    files = {}
    for key in fs.keys():
        item = fs[key]
        if isinstance(item, list):
            item = item[0]
        if item.filename:
            files[key] = {'filename': item.filename, 'data': item.file.read()}
        else:
            fields[key] = item.value

    return fields, files


def _json_error(handler, code, detail):
    """Envía una respuesta JSON de error."""
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps({'detail': detail}).encode())


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            fields, files = _parse_multipart(self)

            if 'excelFile' not in files:
                return _json_error(self, 400, 'Falta el archivo Excel')

            tmp_dir = tempfile.mkdtemp()
            try:
                # Guardar Excel
                excel_info = files['excelFile']
                excel_path = os.path.join(tmp_dir, excel_info['filename'])
                with open(excel_path, 'wb') as f:
                    f.write(excel_info['data'])

                # Textos
                project_title = fields.get('project_title', 'PROYECTO')
                text_sections = {
                    'resumen': fields.get('text_resumen', ''),
                    'estudio_mercado': fields.get('text_estudio', ''),
                    'gestor': fields.get('text_gestor', ''),
                    'riesgos': fields.get('text_riesgos', ''),
                }

                # Fotos por categoría
                image_paths = {'portada': [], 'fachada': [], 'interior': []}
                for key, file_data in files.items():
                    for cat in ['portada', 'fachada', 'interior']:
                        if key.startswith(f'{cat}_'):
                            safe = f"{cat}_{len(image_paths[cat])}_{file_data['filename']}"
                            path = os.path.join(tmp_dir, safe)
                            with open(path, 'wb') as f:
                                f.write(file_data['data'])
                            image_paths[cat].append(path)

                # Parsear Excel y generar PDF
                financial_data = parse_excel(excel_path)
                output_pdf = os.path.join(tmp_dir, 'output.pdf')
                generate_presentation_pdf(
                    output_pdf, financial_data, image_paths,
                    project_title, text_sections,
                )

                with open(output_pdf, 'rb') as f:
                    pdf_bytes = f.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition',
                                 'attachment; filename="Informe_Viabilidad.pdf"')
                self.send_header('Content-Length', str(len(pdf_bytes)))
                self.end_headers()
                self.wfile.write(pdf_bytes)

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        except Exception as e:
            traceback.print_exc()
            _json_error(self, 500, f'Error en la generación: {str(e)}')
