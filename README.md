# Generador de Presentaciones - Grupo Grandir

Aplicación web que genera informes PDF de viabilidad inmobiliaria a partir de datos Excel y fotografías del proyecto.

## Funcionalidades

- 📊 Sube un archivo Excel con datos de viabilidad financiera
- 📸 Añade hasta 3 fotografías del proyecto
- 📝 Personaliza título, gestor y descripción
- 📄 Genera un PDF profesional listo para inversores

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript vanilla
- **Backend**: Python (Vercel Serverless Functions)
- **Librerías**: pandas, openpyxl, reportlab, Pillow

## Despliegue en Vercel

1. Importa este repositorio en [vercel.com](https://vercel.com)
2. Vercel detectará la configuración del `vercel.json` automáticamente
3. Despliega y accede a la URL generada

## Desarrollo local

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```
