# ============================================================
# PORTANALYTICS - ETL DE LIMPIEZA DE DATOS
# Entrada : data/DATOS LOGISTICO PUERTO CARTAGENA (1).csv
# Salida  : datos_logisticos_limpios.csv  (lo lee app.py)
# Uso     : python limpiar_datos.py
# ============================================================

import unicodedata
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
ENTRADA = BASE / "data" / "DATOS LOGISTICO PUERTO CARTAGENA (1).csv"
SALIDA = BASE / "datos_logisticos_limpios.csv"

CATEGORIAS_CARGA = ["Granel Líquido", "Granel Sólido", "Contenedores", "Carga General"]
CATEGORIAS_CLIMA = ["Despejado", "Lluvia Ligera", "Tormenta", "Viento Fuerte"]


def sin_tildes(texto):
    """Minusculas y sin tildes, para comparar nombres escritos de forma distinta."""
    normal = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in normal if unicodedata.category(c) != "Mn").lower().strip()


def estandarizar(serie, categorias, valor_vacio=None):
    """Lleva cada texto a su nombre oficial (ignora mayusculas, tildes y espacios)."""
    mapa = {sin_tildes(c): c for c in categorias}
    return serie.map(lambda v: mapa.get(sin_tildes(v), v) if pd.notna(v) else valor_vacio)


# ------------------------------------------------------------
# 1. EXTRACCION
# ------------------------------------------------------------
df = pd.read_csv(ENTRADA)
print(f"Registros leidos: {len(df)} | columnas: {len(df.columns)}")

# ------------------------------------------------------------
# 2. TRANSFORMACION
# ------------------------------------------------------------

# 2.1 Fechas y horas en formato fecha-hora.
df["Hora_Llegada"] = pd.to_datetime(df["Hora_Llegada"], errors="coerce")
df["Hora_Atraque"] = pd.to_datetime(df["Hora_Atraque"], errors="coerce")

# 2.2 Columnas numericas con tipo numerico.
for col in ["Tiempo_Espera_Horas", "Tiempo_Muelle_Horas", "TEUs_Ocupados"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 2.3 Textos: sin espacios sobrantes y con nombres uniformes.
for col in ["ID_Registro", "Buque", "Tipo_Carga", "Condicion_Climatica"]:
    df[col] = df[col].astype("string").str.strip()
df["Tipo_Carga"] = estandarizar(df["Tipo_Carga"], CATEGORIAS_CARGA)
df["Condicion_Climatica"] = estandarizar(df["Condicion_Climatica"], CATEGORIAS_CLIMA)

# 2.4 Duplicados por ID_Registro.
duplicados = int(df.duplicated(subset="ID_Registro").sum())
df = df.drop_duplicates(subset="ID_Registro", keep="first")

# 2.5 Tipo de carga vacio -> "Sin especificar".
cargas_vacias = int(df["Tipo_Carga"].isna().sum())
df["Tipo_Carga"] = df["Tipo_Carga"].fillna("Sin especificar")

# 2.6 Tiempo de espera vacio -> se calcula como Hora_Atraque - Hora_Llegada
#     (si tampoco existe la hora de atraque, se deja vacio).
vacio = df["Tiempo_Espera_Horas"].isna()
calculable = vacio & df["Hora_Atraque"].notna() & df["Hora_Llegada"].notna()
espera_calculada = (df["Hora_Atraque"] - df["Hora_Llegada"]).dt.total_seconds() / 3600
df.loc[calculable, "Tiempo_Espera_Horas"] = espera_calculada[calculable].round(2)
esperas_calculadas = int(calculable.sum())
esperas_sin_resolver = int(df["Tiempo_Espera_Horas"].isna().sum())

# 2.7 Tiempo de muelle negativo -> promedio de los valores validos (positivos).
negativos = df["Tiempo_Muelle_Horas"] < 0
promedio_muelle = round(df.loc[df["Tiempo_Muelle_Horas"] > 0, "Tiempo_Muelle_Horas"].mean(), 2)
df.loc[negativos, "Tiempo_Muelle_Horas"] = promedio_muelle
muelles_corregidos = int(negativos.sum())

# 2.8 Campo derivado: hora del dia de la llegada (0-23).
df["Hora_del_Dia"] = df["Hora_Llegada"].dt.hour

# ------------------------------------------------------------
# 3. CARGA
# ------------------------------------------------------------
# app.py recalcula Hora_del_Dia, por eso no se guarda en el CSV.
df.drop(columns=["Hora_del_Dia"]).to_csv(SALIDA, index=False)

print("---------------- RESUMEN DE LA LIMPIEZA ----------------")
print(f"Duplicados eliminados ............ {duplicados}")
print(f"Tipos de carga vacios -> 'Sin especificar' ... {cargas_vacias}")
print(f"Tiempos de espera calculados ..... {esperas_calculadas}")
print(f"Tiempos de espera sin resolver ... {esperas_sin_resolver} (se excluyen de los promedios)")
print(f"Tiempos de muelle negativos -> {promedio_muelle} h ... {muelles_corregidos}")
print(f"Registros finales ................ {len(df)}")
print(f"Archivo guardado en: {SALIDA}")