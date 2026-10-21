import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------
# CONFIGURACIÓN
# --------------------------
st.set_page_config(
    page_title="PortAnalytics",
    page_icon="⚓",
    layout="wide"
)

# --------------------------
# CARGA DE DATOS
# --------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("datos_logisticos_limpios.csv")    
    df["Hora_Llegada"] = pd.to_datetime(df["Hora_Llegada"], errors="coerce")
    df["Hora_Atraque"] = pd.to_datetime(df["Hora_Atraque"], errors="coerce")
    df["Hora_del_Dia"] = df["Hora_Llegada"].dt.hour
    return df

df = cargar_datos()

# --------------------------
# TÍTULO Y PRESENTACIÓN
# --------------------------
st.title("⚓ PortAnalytics — Análisis de Operaciones Portuarias")

st.markdown("""
En este tablero presento el análisis de los tiempos de espera, permanencia en muelle 
y volumen de contenedores (TEUs) registrados en el puerto de Cartagena. La información 
fue procesada a partir de datos históricos para identificar cuellos de botella y 
relacionarlos con el tipo de carga y las condiciones climáticas.

> Trabajo realizado para la asignatura de Ciencia de Datos I — 5to semestre Ingeniería de Software
""")

st.divider()

# --------------------------
# RESUMEN GENERAL
# --------------------------
st.subheader("📊 Resumen del período analizado")

tiempo_espera_prom = round(df["Tiempo_Espera_Horas"].mean(), 2)
tiempo_muelle_prom = round(df["Tiempo_Muelle_Horas"].mean(), 1)
total_teus = int(df["TEUs_Ocupados"].sum())
umbral = 3.0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Tiempo de espera promedio", f"{tiempo_espera_prom} h")
    if tiempo_espera_prom > umbral:
        st.warning("Supera el límite de 3 h")
    else:
        st.success("Dentro del rango aceptable")

with col2:
    st.metric("Tiempo en muelle promedio", f"{tiempo_muelle_prom} h")
    st.caption("Incluye maniobras de carga y descarga")

with col3:
    st.metric("Total TEUs movilizados", f"{total_teus:,}")

st.divider()

# --------------------------
# ALERTAS
# --------------------------
demoras = df[df["Tiempo_Espera_Horas"] > umbral]
if not demoras.empty:
    st.subheader("⚠️ Demoras registradas")
    st.info(f"Se encontraron {len(demoras)} registros con espera mayor a {umbral} horas")
    st.dataframe(
        demoras[["ID_Registro", "Buque", "Tiempo_Espera_Horas", "Condicion_Climatica"]],
        use_container_width=True
    )

st.divider()

# --------------------------
# GRÁFICA 1: ESPERA POR TIPO DE CARGA
# --------------------------
st.subheader("1. Tiempo de espera según tipo de carga")

espera_carga = df.groupby("Tipo_Carga")["Tiempo_Espera_Horas"].mean().reset_index()
espera_carga = espera_carga.sort_values("Tiempo_Espera_Horas", ascending=False)

fig1 = px.bar(
    espera_carga,
    x="Tipo_Carga",
    y="Tiempo_Espera_Horas",
    color="Tipo_Carga",
    title="Promedio de horas de espera por categoría",
    labels={
        "Tipo_Carga": "Tipo de Carga",
        "Tiempo_Espera_Horas": "Horas en espera"
    },
    color_discrete_map={
        "Granel Líquido": "#D0021B",
        "Granel Sólido": "#50E3C2",
        "Carga General": "#4A90E2",
        "Contenedores": "#F5A623",
        "Sin especificar": "#9B9B9B"
    }
)
fig1.update_layout(showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("""
> Se observa que la carga de **granel líquido** registra los tiempos de espera más altos,
> seguido por granel sólido. Los contenedores presentan un comportamiento intermedio
> que igual requiere seguimiento.
""")

st.divider()

# --------------------------
# GRÁFICA 2: HORAS PICO
# --------------------------
st.subheader("2. Horas de mayor llegada de buques")

llegadas_hora = df.groupby("Hora_del_Dia").size().reset_index(name="Cantidad_Buques")

fig2 = px.line(
    llegadas_hora,
    x="Hora_del_Dia",
    y="Cantidad_Buques",
    markers=True,
    title="Distribución de llegadas a lo largo del día",
    labels={
        "Hora_del_Dia": "Hora (0 a 23)",
        "Cantidad_Buques": "Número de buques"
    },
    color_discrete_sequence=["#27AE60"]
)
fig2.update_layout(xaxis=dict(tickmode="linear", dtick=2))
st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
> Las horas con mayor afluencia se presentan entre las **18:00 y las 21:00**.
> Se recomienda reforzar la disponibilidad de personal en el turno de tarde/noche.
""")

st.divider()

# --------------------------
# GRÁFICA 3: CLIMA
# --------------------------
st.subheader("3. Efecto de las condiciones climáticas")

clima_espera = df.groupby("Condicion_Climatica")["Tiempo_Espera_Horas"].mean().reset_index()

fig3 = px.bar(
    clima_espera,
    x="Condicion_Climatica",
    y="Tiempo_Espera_Horas",
    color="Condicion_Climatica",
    title="Comportamiento del tiempo de espera según el clima",
    labels={
        "Condicion_Climatica": "Estado del tiempo",
        "Tiempo_Espera_Horas": "Horas promedio de espera"
    },
    color_discrete_map={
        "Despejado": "#F1C40F",
        "Lluvia Ligera": "#3498DB",
        "Tormenta": "#E74C3C",
        "Viento Fuerte": "#9B59B6"
    }
)
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("""
> Los días con **tormenta y viento fuerte** muestran los mayores tiempos de espera.
> Es necesario planificar con anticipación cuando se pronostiquen estas condiciones.
""")

st.divider()

# --------------------------
# CONCLUSIONES
# --------------------------
st.subheader("📝 Conclusiones del análisis")

st.markdown("""
1. El tipo de carga influye directamente en el tiempo de espera: el **granel líquido** requiere mayor atención.
2. Existe mayor llegada de buques en el horario de **tarde y noche**; distribuir recursos podría reducir colas.
3. El clima adverso —especialmente tormenta y viento fuerte— prolonga los tiempos de espera y debe considerarse en la planificación diaria.
4. Se recomienda mantener el umbral de **3 horas** como límite aceptable de espera para activar planes de contingencia.
""")

st.caption("PortAnalytics | Datos procesados con Python y Pandas | Trabajo académico — 2026")