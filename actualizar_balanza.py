import os
import time
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.environ.get("INEGI_TOKEN", "").strip("[]")
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

def dividir_en_lotes(lista, tamano=10):
    for i in range(0, len(lista), tamano):
        yield lista[i:i + tamano]

def obtener_datos_inegi():
    if not TOKEN:
        raise ValueError("Falta configurar el secreto INEGI_TOKEN en GitHub.")

    lista_ids = [x.strip() for x in IDS_SELECCIONADOS.split(",") if x.strip()]
    registros_limpios = []

    for lote in dividir_en_lotes(lista_ids, 10):
        ids_str = ",".join(lote)
        url = (
            f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
            f"INDICATOR/{ids_str}/{IDIOMA}/{AREA_GEOGRAFICA}/false/"
            f"BIE/2.0/{TOKEN}?type=json"
        )

        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()
        datos_crudos = respuesta.json()

        for serie in datos_crudos.get("Series", []):
            indicador_id = serie.get("INDICADOR")
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

        time.sleep(1)

    df = pd.DataFrame(registros_limpios)
    return df.sort_values(by=["periodo", "indicador_id"], ascending=[False, True])

if __name__ == "__main__":
    df_balanza = obtener_datos_inegi()
    df_balanza.to_json("balanza_comercial_mx.json", orient="records", force_ascii=False, indent=2)
    print(f"[{datetime.now()}] Éxito: {len(df_balanza)} registros guardados.")
