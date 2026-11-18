import os
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.environ.get("INEGI_TOKEN", "").strip("[]")

# Tus 20 indicadores exactos de la URL verificada
IDS = "203933,203940,203941,203943,203935,203934,203936,203937,203938,203939,203942,203944,203945,206146,206147,206148,206149,206150,206151,206159"

def obtener_datos_inegi():
    if not TOKEN:
        raise ValueError("Falta configurar el secreto INEGI_TOKEN en GitHub.")

    url = (
        f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
        f"INDICATOR/{IDS}/es/0/false/BIE-BISE/2.0/{TOKEN}?type=json"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    respuesta = requests.get(url, headers=headers, timeout=45)
    respuesta.raise_for_status()
    datos_crudos = respuesta.json()

    registros_limpios = []
    for serie in datos_crudos.get("Series", []):
        indicador_id = str(serie.get("INDICADOR"))
        ultima_actualizacion = serie.get("LASTUPDATE")

        for obs in serie.get("OBSERVATIONS", []):
            periodo = obs.get("TIME_PERIOD")
            valor_str = obs.get("OBS_VALUE")
            estatus = obs.get("OBS_STATUS")

            try:
                valor = float(valor_str) if valor_str not in (None, "", "C") else None
            except ValueError:
                valor = None

            registros_limpios.append({
                "indicador_id": indicador_id,
                "periodo": periodo,
                "valor": valor,
                "estatus_dato": estatus,
                "fecha_actualizacion_inegi": ultima_actualizacion
            })

    if not registros_limpios:
        raise RuntimeError("La API respondió sin observaciones.")

    df = pd.DataFrame(registros_limpios)
    return df.sort_values(by=["periodo", "indicador_id"], ascending=[False, True])

if __name__ == "__main__":
    df_balanza = obtener_datos_inegi()
    df_balanza.to_json("balanza_comercial_mx.json", orient="records", force_ascii=False, indent=2)
    print(f"[{datetime.now()}] Éxito: {len(df_balanza)} registros guardados de {df_balanza['indicador_id'].nunique()} indicadores.")
