import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------
# CONFIGURACIÓN DE LA PÁGINA
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
    # Convertir columnas de fecha/hora si existen
    if "Fecha_Llegada" in df.columns:
        df["Fecha_Llegada"] = pd.to_datetime(df["Fecha_Llegada"], errors="coerce")
    if "Hora_Llegada" in df.columns:
        df["Hora_Llegada"] = pd.to_datetime(df["Hora_Llegada"], errors="coerce")
        df["Hora_del_Dia"] = df["Hora_Llegada"].dt.hour
    return df

df = cargar_datos()

# --------------------------
# FILTROS INTERACTIVOS
# --------------------------
st.sidebar.header("🔍 Filtros de búsqueda")

df_filtrado = df.copy()

# Filtro por tipo de carga
if "Tipo_Carga" in df.columns:
    tipos_carga = sorted(df["Tipo_Carga"].dropna().unique().tolist())
    seleccion_carga = st.sidebar.multiselect(
        "Tipo de Carga",
        options=tipos_carga,
        default=tipos_carga
    )
    df_filtrado = df_filtrado[df_filtrado["Tipo_Carga"].isin(seleccion_carga)]

# Filtro por buque
if "Buque" in df.columns:
    buques = sorted(df["Buque"].dropna().unique().tolist())
    seleccion_buque = st.sidebar.multiselect(
        "Nombre del Buque",
        options=buques,
        default=buques
    )
    df_filtrado = df_filtrado[df_filtrado["Buque"].isin(seleccion_buque)]

# Filtro por condición climática
if "Condicion_Climatica" in df.columns:
    climas = sorted(df["Condicion_Climatica"].dropna().unique().tolist())
    seleccion_clima = st.sidebar.multiselect(
        "Condición Climática",
        options=climas,
        default=climas
    )
    df_filtrado = df_filtrado[df_filtrado["Condicion_Climatica"].isin(seleccion_clima)]

# Mostrar cantidad de registros
st.sidebar.info(f"📋 Mostrando **{len(df_filtrado)}** de {len(df)} registros")

# --------------------------
# TÍTULO Y PRESENTACIÓN
# --------------------------
st.title("⚓ PortAnalytics — Análisis de Operaciones Portuarias")

st.markdown("""
En este tablero se presenta el análisis de los tiempos de espera, permanencia en muelle 
y volumen de contenedores (TEUs) registrados en el puerto de Cartagena. La información 
fue procesada a partir de datos históricos para identificar cuellos de botella y 
relacionarlos con el tipo de carga y las condiciones climáticas.

> Trabajo realizado para la asignatura de Ciencia de Datos I — 5to semestre Ingeniería de Software
""")

st.divider()

# --------------------------
# RESUMEN DE INDICADORES (KPIs)
# --------------------------
st.subheader("📊 Resumen del período analizado")

if not df_filtrado.empty:
    tiempo_espera_prom = round(df_filtrado["Tiempo_Espera_Horas"].mean(), 2)
    tiempo_muelle_prom = round(df_filtrado["Tiempo_Muelle_Horas"].mean(), 1)
    total_teus = int(df_filtrado["TEUs_Ocupados"].sum())
else:
    tiempo_espera_prom = 0
    tiempo_muelle_prom = 0
    total_teus = 0

UMBRAL_DEMORA = 3.0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Tiempo de espera promedio", f"{tiempo_espera_prom} h")
    if tiempo_espera_prom > UMBRAL_DEMORA:
        st.warning(f"⚠️ Supera el límite de {UMBRAL_DEMORA} h")
    else:
        st.success("✅ Dentro del rango aceptable")

with col2:
    st.metric("Tiempo en muelle promedio", f"{tiempo_muelle_prom} h")
    st.caption("Incluye maniobras de carga y descarga")

with col3:
    st.metric("Total TEUs movilizados", f"{total_teus:,}")

st.divider()

# --------------------------
# TABLA DE DEMORAS
# --------------------------
demoras = df_filtrado[df_filtrado["Tiempo_Espera_Horas"] > UMBRAL_DEMORA]

if not demoras.empty:
    st.subheader("⚠️ Demoras registradas")
    st.info(f"Se encontraron **{len(demoras)}** registros con espera mayor a {UMBRAL_DEMORA} horas")
    st.dataframe(
        demoras[["ID_Registro", "Buque", "Tiempo_Espera_Horas", "Condicion_Climatica"]],
        use_container_width=True
    )
else:
    st.success("✅ No se registran demoras en los datos seleccionados")

st.divider()

# --------------------------
# GRÁFICA 1: TIEMPO DE ESPERA POR TIPO DE CARGA
# --------------------------
st.subheader("1. Tiempo de espera por tipo de carga")

if "Tipo_Carga" in df_filtrado.columns and not df_filtrado.empty:
    espera_carga = df_filtrado.groupby("Tipo_Carga")["Tiempo_Espera_Horas"].mean().reset_index()
    espera_carga = espera_carga.sort_values("Tiempo_Espera_Horas", ascending=False)

    fig1 = px.bar(
        espera_carga,
        x="Tipo_Carga",
        y="Tiempo_Espera_Horas",
        color="Tipo_Carga",
        title="Promedio de horas de espera según categoría de carga",
        labels={
            "Tipo_Carga": "Tipo de Carga",
            "Tiempo_Espera_Horas": "Horas en espera (promedio)"
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
    > **Interpretación:** La carga de **granel líquido** registra los tiempos de espera más altos,
    > seguido por granel sólido. Los contenedores presentan un comportamiento intermedio
    > que también requiere seguimiento continuo.
    """)
else:
    st.info("ℹ️ No hay datos suficientes para mostrar esta gráfica.")

st.divider()

# --------------------------
# GRÁFICA 2: DISTRIBUCIÓN DE VOLUMEN (CIRCULAR)
# --------------------------
st.subheader("2. Distribución del volumen por tipo de carga")

if "Tipo_Carga" in df_filtrado.columns and "TEUs_Ocupados" in df_filtrado.columns and not df_filtrado.empty:
    volumen_carga = df_filtrado.groupby("Tipo_Carga")["TEUs_Ocupados"].sum().reset_index()

    fig_pie = px.pie(
        volumen_carga,
        values="TEUs_Ocupados",
        names="Tipo_Carga",
        title="Participación de cada tipo de carga en el movimiento total",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("""
    > **Interpretación:** Este gráfico muestra qué tipo de carga representa la mayor 
    > parte del movimiento del puerto. Ayuda a identificar qué segmentos tienen 
    > mayor peso en la actividad diaria.
    """)
else:
    st.info("ℹ️ No hay datos suficientes para mostrar esta gráfica.")

st.divider()

# --------------------------
# GRÁFICA 3: LLEGADAS POR HORA
# --------------------------
st.subheader("3. Horas de mayor llegada de buques")

if "Hora_del_Dia" in df_filtrado.columns and not df_filtrado.empty:
    llegadas_hora = df_filtrado.groupby("Hora_del_Dia").size().reset_index(name="Cantidad_Buques")

    fig2 = px.line(
        llegadas_hora,
        x="Hora_del_Dia",
        y="Cantidad_Buques",
        markers=True,
        title="Distribución de llegadas a lo largo del día",
        labels={
            "Hora_del_Dia": "Hora del día (0 a 23)",
            "Cantidad_Buques": "Número de buques llegados"
        },
        color_discrete_sequence=["#27AE60"]
    )
    fig2.update_layout(xaxis=dict(tickmode="linear", dtick=2))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    > **Interpretación:** Las horas con mayor afluencia se presentan generalmente 
    > entre las **18:00 y las 21:00**. Se recomienda reforzar la disponibilidad de 
    > personal en el turno de tarde/noche para reducir esperas.
    """)
else:
    st.info("ℹ️ No hay datos de hora para mostrar esta gráfica.")

st.divider()

# --------------------------
# GRÁFICA 4: CLIMA Y ESPERA
# --------------------------
st.subheader("4. Efecto de las condiciones climáticas")

if "Condicion_Climatica" in df_filtrado.columns and not df_filtrado.empty:
    clima_espera = df_filtrado.groupby("Condicion_Climatica")["Tiempo_Espera_Horas"].mean().reset_index()

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
    > **Interpretación:** Los días con **tormenta y viento fuerte** muestran los mayores 
    > tiempos de espera. Es necesario planificar con anticipación cuando se pronostiquen 
    > estas condiciones para evitar acumulación de buques en espera.
    """)
else:
    st.info("ℹ️ No hay datos de clima para mostrar esta gráfica.")

st.divider()

# --------------------------
# SECCIÓN DE CONCLUSIONES
# --------------------------
st.subheader("📝 Conclusiones y Recomendaciones")

if not df_filtrado.empty:
    st.markdown("""
    ### Hallazgos principales:
    
    1. **Tipo de carga y demoras**  
       El **granel líquido** registra los tiempos de espera más elevados, seguido por el granel sólido. 
       Se recomienda revisar y optimizar los procedimientos de atraque para estas cargas prioritarias.
    
    2. **Concentración de llegadas**  
       La mayor cantidad de buques llega entre las **18:00 y las 21:00**. Redistribuir el personal 
       en el turno de tarde/noche podría reducir significativamente los tiempos de espera.
    
    3. **Impacto del clima**  
       Las condiciones adversas —especialmente tormenta y viento fuerte— prolongan los tiempos 
       de espera en más del doble respecto a días despejados. Integrar pronósticos meteorológicos 
       en la planificación diaria es clave para prevenir demoras.
    
    4. **Umbral de control**  
       Se mantiene como meta mantener el tiempo de espera promedio por debajo de las **3 horas**. 
       Cuando se supera este valor, deben activarse procedimientos de contingencia inmediatos.
    """)

    st.info("""
    💡 **Recomendación estratégica:**  
    Implementar un sistema de alertas que avise con anticipación cuando se esperen condiciones 
    climáticas adversas o llegadas múltiples en horarios pico. Esto permitirá reasignar recursos 
    antes de que se formen colas y el impacto sea menor.
    """)
else:
    st.warning("⚠️ No hay registros seleccionados para mostrar conclusiones.")

st.divider()

st.caption("PortAnalytics | Datos procesados con Python y Pandas | Trabajo académico — 2026")