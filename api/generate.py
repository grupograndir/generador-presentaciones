"""
Vercel Serverless Function: /api/generate
Recibe un Excel + fotos opcionales y genera un PDF de viabilidad.
"""

import os
import sys
import shutil
import tempfile
from http.server import BaseHTTPRequestHandler
import cgi
import json

# Añadir el directorio raíz al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_parser import parse_excel
from pdf_generator import generate_presentation_pdf


def parse_multipart(handler):
    """Parsea los datos multipart/form-data del request."""
    content_type = handler.headers.get('content-type', '')
    
    if 'multipart/form-data' not in content_type:
        return {}, {}
    
    # Extraer boundary
    ctype, pdict = cgi.parse_header(content_type)
    if 'boundary' in pdict:
        if isinstance(pdict['boundary'], str):
            pdict['boundary'] = pdict['boundary'].encode('utf-8')
    
    # Leer body
    content_length = int(handler.headers.get('content-length', 0))
    body = handler.rfile.read(content_length)
    
    # Parsear multipart
    environ = {
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': content_type,
        'CONTENT_LENGTH': str(content_length),
    }
    
    fs = cgi.FieldStorage(
        fp=__import__('io').BytesIO(body),
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
            # Parsear multipart
            fields, files = parse_multipart(self)
            
            # Validar que viene el Excel
            if 'excelFile' not in files:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'detail': 'Falta el archivo Excel'}).encode())
                return
            
            # Crear directorio temporal
            tmp_dir = tempfile.mkdtemp()
            
            try:
                # Guardar el Excel
                excel_data = files['excelFile']
                excel_path = os.path.join(tmp_dir, excel_data['filename'])
                with open(excel_path, 'wb') as f:
                    f.write(excel_data['data'])
                
                # Guardar imágenes si existen
                image_paths = []
                for photo_key in ['photo1', 'photo2', 'photo3']:
                    if photo_key in files:
                        photo_data = files[photo_key]
                        photo_path = os.path.join(tmp_dir, photo_data['filename'])
                        with open(photo_path, 'wb') as f:
                            f.write(photo_data['data'])
                        image_paths.append(photo_path)
                
                # Obtener campos de texto
                project_title = fields.get('project_title', 'PROYECTO')
                gestor_name = fields.get('gestor_name', 'GESTOR')
                project_description = fields.get('project_description', '')
                
                # Parsear Excel
                financial_data = parse_excel(excel_path)
                
                # Generar PDF
                output_pdf_path = os.path.join(tmp_dir, 'Informe_Viabilidad_Generado.pdf')
                generate_presentation_pdf(
                    output_pdf_path,
                    financial_data,
                    image_paths,
                    project_title,
                    gestor_name,
                    project_description
                )
                
                # Leer el PDF generado
                with open(output_pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                # Enviar respuesta
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', 'attachment; filename="Informe_Viabilidad.pdf"')
                self.send_header('Content-Length', str(len(pdf_bytes)))
                self.end_headers()
                self.wfile.write(pdf_bytes)
                
            finally:
                # Limpiar archivos temporales
                shutil.rmtree(tmp_dir, ignore_errors=True)
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'detail': str(e)}).encode())
