import pandas as pd
import numpy as np

def extract_first_number_to_right(df, row_idx, col_idx):
    """
    Busca el primer número válido a la derecha de la celda encontrada.
    """
    for c in range(col_idx + 1, len(df.columns)):
        val = df.iloc[row_idx, c]
        if pd.notna(val):
            try:
                # Intenta convertir a float, descartando strings que no sean números
                # Si es un string con comas como separador de miles, limpiarlo
                val_str = str(val).replace(',', '').strip()
                return float(val_str)
            except ValueError:
                continue
    return None

def parse_excel(file_path: str) -> dict:
    """
    Lee celda a celda los datos relevantes del Excel de viabilidad de forma robusta.
    Extrae la Inversión Total, Coste de Terminación, Ventas, Beneficio y ROI,
    buscando en todas las hojas el texto y tomando el primer número a su derecha.
    """
    # Valores por defecto en caso de no encontrar nada
    data = {
        "coste_adquisicion": 0.0,
        "coste_terminacion": 0.0,
        "total_inversion": 0.0,
        "total_ventas": 0.0,
        "beneficio_bruto": 0.0,
        "roi": 0.0,
        "viviendas": [],
        "garajes": [],
        "trasteros": []
    }
    
    found = {k: False for k in ["coste_adquisicion", "coste_terminacion", "total_inversion", "total_ventas", "beneficio_bruto", "roi"]}

    try:
        xl = pd.ExcelFile(file_path)
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            for row in range(len(df)):
                for col in range(len(df.columns)):
                    val = str(df.iloc[row, col]).strip().upper()
                    
                    if not found["total_inversion"] and (val == "INVERSION TOTAL" or val == "TOTAL INVERSION"):
                        num = extract_first_number_to_right(df, row, col)
                        if num is not None:
                            data['total_inversion'] = num
                            found["total_inversion"] = True
                            
                    elif not found["coste_terminacion"] and val == "COSTE TERMINACION":
                        num = extract_first_number_to_right(df, row, col)
                        if num is not None:
                            data['coste_terminacion'] = num
                            found["coste_terminacion"] = True
                            
                    elif not found["coste_adquisicion"] and (val == "COSTE ADQUISICIÓN SUELO + ESTRUCTURA" or val == "COSTE ADQUISICION"):
                        num = extract_first_number_to_right(df, row, col)
                        if num is not None:
                            data['coste_adquisicion'] = num
                            found["coste_adquisicion"] = True
                            
                    elif not found["total_ventas"] and (val == "TOTAL VENTA" or val == "PRECIO VENTA"):
                        num = extract_first_number_to_right(df, row, col)
                        if num is not None:
                            data['total_ventas'] = num
                            found["total_ventas"] = True
                            
                    elif not found["beneficio_bruto"] and val == "BENEFICIO BRUTO":
                        num = extract_first_number_to_right(df, row, col)
                        if num is not None:
                            data['beneficio_bruto'] = num
                            found["beneficio_bruto"] = True
                            
                    elif not found["roi"] and val == "ROI":
                        num = extract_first_number_to_right(df, row, col)
                        if num is not None:
                            data['roi'] = (num * 100) if num <= 1.5 else num
                            found["roi"] = True

            # Extraer listado de propiedades (Tipología)
            header_row_idx = None
            for row in range(min(20, len(df))):
                for col in range(len(df.columns)):
                    if str(df.iloc[row, col]).strip() == "Tipología":
                        header_row_idx = row
                        break
                if header_row_idx is not None:
                    break
                    
            if header_row_idx is not None:
                headers = list(map(str, df.iloc[header_row_idx].tolist()))
                
                for row in range(header_row_idx + 1, len(df)):
                    tipologia_raw = str(df.iloc[row, df.columns.get_loc(df.columns[headers.index("Tipología")])]) if "Tipología" in headers else ""
                    tipologia = tipologia_raw.strip().lower()
                    
                    if not tipologia or tipologia == "nan" or tipologia == "totales" or pd.isna(tipologia_raw):
                        if "Id" in headers:
                            id_val = str(df.iloc[row, df.columns.get_loc(df.columns[headers.index("Id")])])
                            if id_val == "nan" or id_val.lower() == "totales":
                                continue
                        else:
                            # Sin ID y sin tipologia, paramos de buscar en esta tabla
                            continue

                    # Extraer campos clave
                    def get_val(hdr):
                        if hdr in headers:
                            idx = headers.index(hdr)
                            v = df.iloc[row, idx]
                            return v if pd.notna(v) and str(v) != "nan" else ""
                        return ""
                    
                    item = {
                        "Planta": get_val("Planta"),
                        "Puerta": get_val("Puerta"),
                        "Constr.": get_val("Constr."),
                        "Habs": get_val("Habs*"),
                        "Precio": get_val("Precio Medio")
                    }
                    
                    # Formatear números si existen
                    try:
                        if item["Constr."]: item["Constr."] = f"{float(item['Constr.']):.1f} m²"
                    except: pass
                    
                    try:
                        if item["Precio"]: item["Precio"] = f"{float(item['Precio']):,.2f} €"
                    except: pass
                    
                    # Formatear planta/puerta
                    item["Planta"] = str(item["Planta"])
                    item["Puerta"] = str(item["Puerta"])
                    item["Habs"] = str(item["Habs"])

                    # Agrupar según tipología original para respetar formato humano
                    item["Tipología original"] = tipologia_raw
                    
                    if "garaje" in tipologia:
                        data["garajes"].append(item)
                    elif "trastero" in tipologia:
                        data["trasteros"].append(item)
                    else:
                        # Consideramos el resto como viviendas (Piso, ático, bajo...)
                        data["viviendas"].append(item)

        # Si no encontramos coste de adquisición pero sí total inversión y coste de terminación, lo calculamos
        if not found["coste_adquisicion"] and found["total_inversion"] and found["coste_terminacion"]:
            data["coste_adquisicion"] = data["total_inversion"] - data["coste_terminacion"]
            
        # Si no hay coste adquisición pero el total es el mismo que el de adquisición en el formato viejo
        if not found["total_inversion"] and found["coste_adquisicion"] and found["coste_terminacion"]:
            data["total_inversion"] = data["coste_adquisicion"] + data["coste_terminacion"]

        return data

    except Exception as e:
        print(f"Error parsing excel: {e}")
        return data
