import pandas as pd
import numpy as np
from datetime import datetime

# Cargar datos
ruta = "data/DATOS LOGISTICO PUERTO CARTAGENA (1).csv"
df = pd.read_csv(ruta)

# === 1. Corregir nombres de columnas ===
df.columns = [
    "ID_Registro", "Buque", "Tipo_Carga", "Hora_Llegada", 
    "Hora_Atraque", "Tiempo_Espera_Horas", "Tiempo_Muelle_Horas", 
    "TEUs_Ocupados", "Condicion_Climatica"
]

# === 2. Valores nulos ===
# Tiempo de espera nulo → calcularlo desde horas
df["Hora_Llegada"] = pd.to_datetime(df["Hora_Llegada"], errors="coerce")
df["Hora_Atraque"] = pd.to_datetime(df["Hora_Atraque"], errors="coerce")

df["Tiempo_Espera_Horas"] = df.apply(
    lambda fila: (fila["Hora_Atraque"] - fila["Hora_Llegada"]).total_seconds()/3600
    if pd.isna(fila["Tiempo_Espera_Horas"]) and pd.notna(fila["Hora_Atraque"])
    else fila["Tiempo_Espera_Horas"], axis=1
)

# Tiempo de muelle negativo → reemplazar por promedio
promedio_muelle = df[df["Tiempo_Muelle_Horas"] > 0]["Tiempo_Muelle_Horas"].mean()
df["Tiempo_Muelle_Horas"] = df["Tiempo_Muelle_Horas"].apply(
    lambda x: promedio_muelle if x < 0 else x
)

# Tipo de carga vacío → "Sin especificar"
df["Tipo_Carga"] = df["Tipo_Carga"].fillna("Sin especificar")

# === 3. Duplicados ===
df = df.drop_duplicates(subset="ID_Registro", keep="first")

# === 4. Guardar limpios ===
df.to_csv("data/datos_logisticos_limpios.csv", index=False)
print("✅ Datos limpios guardados. Filas:", len(df))