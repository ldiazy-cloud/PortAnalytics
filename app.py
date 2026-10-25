# ============================================================
# PortAnalytics — Sistema de Análisis de Operaciones Portuarias
# Asignatura: Ciencia de Datos I
# Autor: Estudiante de Ingeniería de Software — 5to Semestre
# Fecha: 2026
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------
# CONFIGURACIÓN GLOBAL
# --------------------------
st.set_page_config(
    page_title="PortAnalytics | Análisis Portuario",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# CARGA DE DATOS
# --------------------------
@st.cache_data(show_spinner="Cargando conjunto de datos...")
def cargar_datos():
    df = pd.read_csv("datos_logisticos_limpios.csv")
    
    if "Fecha_Llegada" in df.columns:
        df["Fecha_Llegada"] = pd.to_datetime(df["Fecha_Llegada"], errors="coerce")
    if "Hora_Llegada" in df.columns:
        df["Hora_Llegada"] = pd.to_datetime(df["Hora_Llegada"], errors="coerce")
        df["Hora_del_Dia"] = df["Hora_Llegada"].dt.hour
    
    return df

df = cargar_datos()

# --------------------------
# CONSTANTES
# --------------------------
UMBRAL_CONTROL = 3.0
COLORES_CARGA = {
    "Granel Líquido": "#B91C1C",
    "Granel Sólido": "#0D9488",
    "Contenedores": "#D97706",
    "Carga General": "#2563EB",
    "Sin especificar": "#6B7280"
}
COLORES_CLIMA = {
    "Despejado": "#EAB308",
    "Lluvia Ligera": "#3B82F6",
    "Tormenta": "#DC2626",
    "Viento Fuerte": "#8B5CF6"
}

# --------------------------
# FILTROS
# --------------------------
with st.sidebar:
    st.header("🔍 Panel de Filtros")
    st.markdown("---")
    
    df_filtrado = df.copy()
    
    if "Tipo_Carga" in df.columns:
        lista_cargas = sorted(df["Tipo_Carga"].dropna().unique().tolist())
        filtro_carga = st.multiselect(
            "**Tipo de Carga**",
            options=lista_cargas,
            default=lista_cargas
        )
        df_filtrado = df_filtrado[df_filtrado["Tipo_Carga"].isin(filtro_carga)]
    
    if "Buque" in df.columns:
        lista_buques = sorted(df["Buque"].dropna().unique().tolist())
        filtro_buque = st.multiselect(
            "**Buque**",
            options=lista_buques,
            default=lista_buques
        )
        df_filtrado = df_filtrado[df_filtrado["Buque"].isin(filtro_buque)]
    
    if "Condicion_Climatica" in df.columns:
        lista_clima = sorted(df["Condicion_Climatica"].dropna().unique().tolist())
        filtro_clima = st.multiselect(
            "**Condición Climática**",
            options=lista_clima,
            default=lista_clima
        )
        df_filtrado = df_filtrado[df_filtrado["Condicion_Climatica"].isin(filtro_clima)]
    
    st.markdown("---")
    total = len(df)
    mostrados = len(df_filtrado)
    st.info(f"📋 {mostrados} de {total} registros mostrados")

# --------------------------
# CABECERA
# --------------------------
st.title("⚓ PortAnalytics — Sistema de Análisis Logístico Portuario")
st.markdown("""
> **Puerto de Cartagena de Indias** · Monitoreo de Tiempos de Operación y Desempeño

Este tablero presenta el procesamiento y análisis de datos históricos de operación portuaria, 
con el propósito de identificar cuellos de botella, evaluar el impacto del tipo de carga y 
condiciones climáticas, y proponer mejoras en los tiempos de espera y atraque.

*Proyecto — Ciencia de Datos I · Ingeniería de Software*
""")
st.divider()

# --------------------------
# KPIs
# --------------------------
st.subheader("📊 Indicadores Clave de Desempeño")

if not df_filtrado.empty:
    espera_prom = round(df_filtrado["Tiempo_Espera_Horas"].mean(), 2)
    muelle_prom = round(df_filtrado["Tiempo_Muelle_Horas"].mean(), 1)
    teus_total = int(df_filtrado["TEUs_Ocupados"].sum())
    cant_demoras = len(df_filtrado[df_filtrado["Tiempo_Espera_Horas"] > UMBRAL_CONTROL])
else:
    espera_prom = muelle_prom = teus_total = cant_demoras = 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Tiempo de Espera Promedio", f"{espera_prom} h", f"Meta: < {UMBRAL_CONTROL} h")
    st.success("✅ Dentro del estándar") if espera_prom <= UMBRAL_CONTROL else st.warning("⚠️ Fuera de rango")

with c2:
    st.metric("Estancia en Muelle", f"{muelle_prom} h")
    st.caption("Incluye maniobras")

with c3:
    st.metric("TEUs Movilizados", f"{teus_total:,}")

with c4:
    st.metric("Casos con Demora", f"{cant_demoras}")

st.divider()

# --------------------------
# DEMORAS
# --------------------------
st.subheader("⚠️ Seguimiento de Operaciones con Demora")

if cant_demoras > 0:
    st.warning(f"Se detectaron **{cant_demoras}** operaciones que superaron {UMBRAL_CONTROL} horas.")
    tabla = df_filtrado[
        df_filtrado["Tiempo_Espera_Horas"] > UMBRAL_CONTROL
    ].sort_values("Tiempo_Espera_Horas", ascending=False)[
        ["ID_Registro", "Buque", "Tipo_Carga", "Tiempo_Espera_Horas", "Condicion_Climatica"]
    ]
    st.dataframe(tabla, use_container_width=True, hide_index=True)
else:
    st.success("✅ Sin demoras que reportar. Desempeño óptimo.")

st.divider()

# --------------------------
# GRÁFICA 1: ESPERA POR CARGA
# --------------------------
st.subheader("1. Tiempo de Espera por Tipo de Carga")

if "Tipo_Carga" in df_filtrado.columns and not df_filtrado.empty:
    g1 = df_filtrado.groupby("Tipo_Carga")["Tiempo_Espera_Horas"].mean().reset_index()
    g1 = g1.sort_values("Tiempo_Espera_Horas", ascending=False)
    
    fig1 = px.bar(
        g1, x="Tipo_Carga", y="Tiempo_Espera_Horas",
        color="Tipo_Carga", color_discrete_map=COLORES_CARGA,
        labels={"Tiempo_Espera_Horas": "Horas Promedio"}, text_auto=".2f"
    )
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("""
    > **Análisis:** El **granel líquido** registra los mayores tiempos de espera, 
    > seguido por granel sólido. Constituyen el foco principal de optimización.
    """)

st.divider()

# --------------------------
# GRÁFICA 2: DISTRIBUCIÓN CIRCULAR
# --------------------------
st.subheader("2. Distribución del Volumen Movilizado")

if "Tipo_Carga" in df_filtrado.columns and "TEUs_Ocupados" in df_filtrado.columns and not df_filtrado.empty:
    g2 = df_filtrado.groupby("Tipo_Carga")["TEUs_Ocupados"].sum().reset_index()
    
    fig2 = px.pie(
        g2, values="TEUs_Ocupados", names="Tipo_Carga",
        color="Tipo_Carga", color_discrete_map=COLORES_CARGA,
        title="Participación por Tipo de Carga", hole=0.3
    )
    fig2.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --------------------------
# GRÁFICA 3: HORARIOS PICO
# --------------------------
st.subheader("3. Patrón de Llegadas y Horarios Pico")

if "Hora_del_Dia" in df_filtrado.columns and not df_filtrado.empty:
    g3 = df_filtrado.groupby("Hora_del_Dia").size().reset_index(name="Cantidad")
    
    fig3 = px.line(
        g3, x="Hora_del_Dia", y="Cantidad", markers=True,
        labels={"Cantidad": "Número de Buques"}, color_discrete_sequence=["#0D9488"]
    )
    fig3.update_layout(xaxis=dict(tickmode="linear", dtick=2))
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("""
    > **Análisis:** La mayor afluencia se concentra entre las **18:00 y 21:00**. 
    > Se recomienda reforzar personal en el turno de tarde/noche.
    """)

st.divider()

# --------------------------
# GRÁFICA 4: IMPACTO CLIMÁTICO
# --------------------------
st.subheader("4. Influencia de las Condiciones Climáticas")

if "Condicion_Climatica" in df_filtrado.columns and not df_filtrado.empty:
    g4 = df_filtrado.groupby("Condicion_Climatica")["Tiempo_Espera_Horas"].mean().reset_index()
    g4 = g4.sort_values("Tiempo_Espera_Horas", ascending=False)
    
    fig4 = px.bar(
        g4, x="Condicion_Climatica", y="Tiempo_Espera_Horas",
        color="Condicion_Climatica", color_discrete_map=COLORES_CLIMA,
        labels={"Tiempo_Espera_Horas": "Horas Promedio"}, text_auto=".2f"
    )
    fig4.update_layout(showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("""
    > **Análisis:** Tormenta y viento fuerte duplican los tiempos de espera. 
    > Integrar pronósticos meteorológicos en la planificación es clave.
    """)

st.divider()

# --------------------------
# CONCLUSIONES
# --------------------------
st.subheader("📝 Conclusiones y Recomendaciones")

if not df_filtrado.empty:
    st.markdown("""
    ### Hallazgos Relevantes:
    1. **Carga crítica:** Granel líquido y granel sólido presentan los mayores tiempos de espera.
       Requieren revisión de protocolos de atraque.
    2. **Concentración horaria:** Mayor llegada de buques en horario de tarde/noche.
       Redistribuir recursos en estos turnos reducirá colas.
    3. **Impacto climático:** Condiciones adversas aumentan los tiempos de espera de forma notable.
    4. **Umbral de control:** Las 3.0 horas se confirman como meta válida para activar contingencias.
    
    ### Recomendaciones Estratégicas:
    - 📊 Incorporar pronósticos meteorológicos en la programación semanal
    - 👥 Reforzar dotación entre las 18:00 y 21:00
    - ⚓ Establecer protocolo prioritario para granel líquido
    - 🚨 Implementar alertas automáticas al superar las 3 horas de espera
    """)
    
    st.success("""
    ✅ **Conclusión General:** PortAnalytics demuestra ser una herramienta funcional 
    de apoyo a la toma de decisiones. Se recomienda su expansión con datos en tiempo real.
    """)

st.divider()

st.caption("PortAnalytics v1.0 · Ciencia de Datos I · Universidad de Cartagena · 2026")
