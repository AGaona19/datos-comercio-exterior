import os
import time
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.environ.get("4e124a28-6ca3-69e7-807f-a071416f495d", "").strip("[]")
IDIOMA = "es"
AREA_GEOGRAFICA = "00"

IDS_SELECCIONADOS = (
    "897,206784,206785,375922,912,913,914,924,206754,206755,"
    "921,922,923,127598,915,916,917,127595,206756,206757,"
    "925,926,127599,927,918,919,920,932,206758,206759,"
    "929,930,931,127600,127601,206128,206129,933,206130,206131,"
    "934,206132,206133,935,127602,206134,206135,936,206136,206137,"
    "937,206138,206139,938,127603,206140,206141,939,206142,206143,"
    "940,206144,206145,941"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

def consultar_indicador(ind_id):
    # Intenta primero en BIE y si no devuelve JSON válido, intenta en BISE
    for fuente in ["BIE", "BISE"]:
        url = (
            f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
            f"INDICATOR/{ind_id}/{IDIOMA}/{AREA_GEOGRAFICA}/false/"
            f"{fuente}/2.0/{TOKEN}?type=json"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=25)
            if resp.status_code == 200 and resp.text.strip().startswith("{"):
                data = resp.json()
                if "Series" in data and len(data["Series"]) > 0:
                    return data["Series"]
        except Exception:
            continue
    return []

def obtener_datos_inegi():
    if not TOKEN:
        raise ValueError("Falta configurar el secreto INEGI_TOKEN en GitHub.")

    lista_ids = [x.strip() for x in IDS_SELECCIONADOS.split(",") if x.strip()]
    registros_limpios = []
    exitosos = 0

    for ind_id in lista_ids:
        series = consultar_indicador(ind_id)
        if series:
            exitosos += 1
            for serie in series:
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
                        "indicador_id": str(ind_id),
                        "periodo": periodo,
                        "valor": valor,
                        "estatus_dato": estatus,
                        "fecha_actualizacion_inegi": ultima_actualizacion
                    })
        else:
            print(f"Aviso: El indicador {ind_id} no devolvió datos en BIE ni BISE.")

        time.sleep(0.3)

    if not registros_limpios:
        raise RuntimeError("No se pudo extraer ningún dato. Verifica que el token del INEGI sea válido y esté activo.")

    df = pd.DataFrame(registros_limpios)
    print(f"Indicadores descargados con éxito: {exitosos} de {len(lista_ids)}")
    return df.sort_values(by=["periodo", "indicador_id"], ascending=[False, True])

if __name__ == "__main__":
    df_balanza = obtener_datos_inegi()
    df_balanza.to_json("balanza_comercial_mx.json", orient="records", force_ascii=False, indent=2)
    print(f"[{datetime.now()}] Éxito: {len(df_balanza)} registros guardados.")
