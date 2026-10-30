# ============================================================
# PORTANALYTICS
# Dashboard de analítica logística portuaria
# Proyecto académico - Ciencia de Datos I
# ============================================================

from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="PortAnalytics",
    page_icon="⚓",
    layout="wide"
)

UMBRAL_CONTROL = 3.0
MUELLES_POR_DEFECTO = 5
NOMBRE_CSV = "datos_logisticos_limpios.csv"

CARPETA_APP = Path(__file__).resolve().parent

RUTAS_CSV = [
    CARPETA_APP / NOMBRE_CSV,
    CARPETA_APP / "data" / NOMBRE_CSV,
    Path.cwd() / NOMBRE_CSV,
    Path.cwd() / "data" / NOMBRE_CSV,
]

ARCHIVO_CSV = next(
    (ruta for ruta in RUTAS_CSV if ruta.is_file()),
    None
)

COLORES_CARGA = {
    "Granel Líquido": "#B91C1C",
    "Granel Solido": "#0D9488",
    "Granel Sólido": "#0D9488",
    "Contenedores": "#D97706",
    "Carga General": "#2563EB",
    "Sin especificar": "#6B7280",
}

COLORES_CLIMA = {
    "Despejado": "#EAB308",
    "Lluvia Ligera": "#3B82F6",
    "Tormenta": "#DC2626",
    "Viento Fuerte": "#8B5CF6",
    "Sin especificar": "#6B7280",
}

COLUMNAS_REQUERIDAS = [
    "ID_Registro",
    "Buque",
    "Tipo_Carga",
    "Hora_Llegada",
    "Tiempo_Espera_Horas",
    "Tiempo_Muelle_Horas",
    "TEUs_Ocupados",
    "Condicion_Climatica",
]

COLUMNAS_NUMERICAS = [
    "Tiempo_Espera_Horas",
    "Tiempo_Muelle_Horas",
    "TEUs_Ocupados",
]

COLUMNAS_TEXTO = [
    "ID_Registro",
    "Buque",
    "Tipo_Carga",
    "Condicion_Climatica",
]


# ============================================================
# 2. FUNCIÓN PARA CARGAR Y VALIDAR LOS DATOS
# ============================================================

@st.cache_data(show_spinner="Cargando y validando los datos...")
def cargar_datos(ruta_archivo):

    df = pd.read_csv(ruta_archivo)

    # Comprobar que existan las columnas necesarias.
    faltantes = [
        columna
        for columna in COLUMNAS_REQUERIDAS
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "El CSV no contiene las siguientes columnas obligatorias: "
            + ", ".join(faltantes)
        )

    df = df.copy()

    diagnostico = {
        "total_registros": len(df),
        "duplicados_id": 0,
        "fechas_invalidas": 0,
        "valores_negativos": {},
        "valores_ausentes": {},
    }

    # Normalizar las columnas de texto.
    for columna in COLUMNAS_TEXTO:

        df[columna] = (
            df[columna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Convertir la fecha.
    df["Hora_Llegada"] = pd.to_datetime(
        df["Hora_Llegada"],
        errors="coerce"
    )

    # Convertir las columnas numéricas.
    for columna in COLUMNAS_NUMERICAS:

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        )

    # Detectar valores negativos.
    for columna in COLUMNAS_NUMERICAS:

        mascara = df[columna] < 0

        diagnostico["valores_negativos"][columna] = int(
            mascara.sum()
        )

        # Un valor negativo no se considera una duración o cantidad válida.
        df.loc[mascara, columna] = float("nan")

    # Detectar identificadores duplicados.
    ids_validos = df.loc[
        df["ID_Registro"].notna(),
        "ID_Registro"
    ]

    diagnostico["duplicados_id"] = int(
        ids_validos.duplicated().sum()
    )

    # Detectar fechas inválidas o ausentes.
    diagnostico["fechas_invalidas"] = int(
        df["Hora_Llegada"].isna().sum()
    )

    # Contar valores numéricos ausentes.
    for columna in COLUMNAS_NUMERICAS:

        diagnostico["valores_ausentes"][columna] = int(
            df[columna].isna().sum()
        )

    # Etiquetar campos de texto vacíos.
    for columna in COLUMNAS_TEXTO:

        df[columna] = (
            df[columna]
            .fillna("Sin especificar")
            .astype(str)
        )

    # Crear una columna con la hora de llegada.
    df["Hora_del_Dia"] = df["Hora_Llegada"].dt.hour

    return df, diagnostico


# ============================================================
# 3. ENCABEZADO DEL DASHBOARD
# ============================================================

st.title("⚓ PortAnalytics")

st.subheader(
    "Dashboard de analítica logística portuaria"
)

st.markdown(
    """
    Esta aplicación permite explorar operaciones portuarias,
    analizar tiempos de espera, revisar la permanencia en muelle
    e identificar posibles demoras críticas.

    Los resultados dependen de la calidad y el contenido
    de los datos proporcionados.
    """
)

st.divider()


# ============================================================
# 4. CARGAR EL ARCHIVO CSV
# ============================================================

if ARCHIVO_CSV is None:

    st.error(
        "No se encontró el archivo "
        "'datos_logisticos_limpios.csv'."
    )

    st.markdown(
        """
        **Solución:**

        1. Comprueba que el archivo CSV exista.
        2. Colócalo en la misma carpeta que `app.py`
           o dentro de la carpeta `data`.
        3. Verifica que el nombre sea exactamente
           `datos_logisticos_limpios.csv`.
        """
    )

    st.stop()


try:

    df, diagnostico = cargar_datos(
        str(ARCHIVO_CSV)
    )

except Exception as error:

    st.error(
        f"No fue posible cargar los datos: {error}"
    )

    st.stop()


if df.empty:

    st.error(
        "El archivo CSV no contiene registros."
    )

    st.stop()


# ============================================================
# 5. DIAGNÓSTICO DE CALIDAD DE LOS DATOS
# ============================================================

with st.expander(
    "🔎 Diagnóstico de calidad de los datos",
    expanded=False
):

    st.write(
        f"**Archivo utilizado:** {ARCHIVO_CSV.name}"
    )

    st.write(
        f"**Registros cargados:** "
        f"{diagnostico['total_registros']}"
    )

    st.write(
        f"**Identificadores duplicados:** "
        f"{diagnostico['duplicados_id']}"
    )

    st.write(
        f"**Fechas inválidas o ausentes:** "
        f"{diagnostico['fechas_invalidas']}"
    )

    st.markdown("**Valores numéricos ausentes:**")

    for columna, cantidad in (
        diagnostico["valores_ausentes"].items()
    ):

        st.write(
            f"- {columna}: {cantidad}"
        )

    st.markdown("**Valores negativos detectados:**")

    for columna, cantidad in (
        diagnostico["valores_negativos"].items()
    ):

        st.write(
            f"- {columna}: {cantidad}"
        )

    st.caption(
        "Los valores negativos se excluyen de los cálculos "
        "numéricos. Los registros no se eliminan automáticamente."
    )


# ============================================================
# 6. FILTROS LATERALES
# ============================================================

tipos_carga = sorted(
    df["Tipo_Carga"].unique().tolist()
)

buques = sorted(
    df["Buque"].unique().tolist()
)

climas = sorted(
    df["Condicion_Climatica"].unique().tolist()
)


def restablecer_filtros():

    st.session_state["f_carga"] = tipos_carga.copy()

    st.session_state["f_buque"] = buques.copy()

    st.session_state["f_clima"] = climas.copy()

    st.session_state["f_muelles"] = MUELLES_POR_DEFECTO


# Inicializar los filtros.
if "f_carga" not in st.session_state:
    st.session_state["f_carga"] = tipos_carga.copy()

if "f_buque" not in st.session_state:
    st.session_state["f_buque"] = buques.copy()

if "f_clima" not in st.session_state:
    st.session_state["f_clima"] = climas.copy()

if "f_muelles" not in st.session_state:
    st.session_state["f_muelles"] = MUELLES_POR_DEFECTO


st.sidebar.header("🔍 Filtros de operaciones")

cargas_seleccionadas = st.sidebar.multiselect(
    "Tipo de carga",
    options=tipos_carga,
    key="f_carga"
)

buques_seleccionados = st.sidebar.multiselect(
    "Buque",
    options=buques,
    key="f_buque"
)

climas_seleccionados = st.sidebar.multiselect(
    "Condición climática",
    options=climas,
    key="f_clima"
)

st.sidebar.divider()

st.sidebar.subheader(
    "⚙ Parámetros del modelo"
)

n_muelles = st.sidebar.number_input(
    "Número de muelles disponibles (supuesto)",
    min_value=1,
    max_value=100,
    step=1,
    key="f_muelles",
    help=(
        "Es un supuesto para la estimación, "
        "no necesariamente el número real de muelles."
    )
)

st.sidebar.caption(
    "La utilización calculada es una estimación teórica."
)

st.sidebar.button(
    "Restablecer filtros",
    on_click=restablecer_filtros,
    use_container_width=True
)


# ============================================================
# 7. APLICAR LOS FILTROS
# ============================================================

df_filtrado = df[
    df["Tipo_Carga"].isin(cargas_seleccionadas)
    & df["Buque"].isin(buques_seleccionados)
    & df["Condicion_Climatica"].isin(climas_seleccionados)
].copy()

st.caption(
    f"Operaciones seleccionadas: "
    f"{len(df_filtrado)} de {len(df)}"
)


# ============================================================
# 8. PREPARAR LOS INDICADORES
# ============================================================

espera_prom = None
muelle_prom = None
ocupacion = None
eficiencia = None

teus_total = 0.0
cant_demoras = 0

# Tablas vacías para evitar errores si no hay datos.
espera_por_carga = pd.DataFrame(
    columns=["Tipo_Carga", "Tiempo_Espera_Horas"]
)

espera_por_clima = pd.DataFrame(
    columns=[
        "Condicion_Climatica",
        "Espera_Promedio",
        "Casos"
    ]
)

llegadas_por_hora = pd.DataFrame(
    {
        "Hora_del_Dia": list(range(24)),
        "Cantidad": [0] * 24,
    }
)

if not df_filtrado.empty:

    # Promedio de espera.
    espera_prom = (
        df_filtrado["Tiempo_Espera_Horas"].mean()
    )

    # Promedio de permanencia en muelle.
    muelle_prom = (
        df_filtrado["Tiempo_Muelle_Horas"].mean()
    )

    # Seleccionar exclusivamente operaciones de contenedores.
    contenedores = df_filtrado[
        df_filtrado["Tipo_Carga"].str.strip().str.casefold()
        == "contenedores"
    ].copy()

    # Suma de TEUs registrados en contenedores.
    teus_calculados = contenedores[
        "TEUs_Ocupados"
    ].sum(min_count=1)

    if pd.notna(teus_calculados):
        teus_total = float(teus_calculados)

    # Número de operaciones que superan el umbral.
    cant_demoras = int(
        (
            df_filtrado["Tiempo_Espera_Horas"]
            > UMBRAL_CONTROL
        ).sum()
    )

    # Estimación teórica de utilización de muelles.
    # Se utiliza el período total del archivo.
    fechas_validas = df["Hora_Llegada"].dropna()

    if len(fechas_validas) >= 2:

        horas_periodo = (
            fechas_validas.max() - fechas_validas.min()
        ).total_seconds() / 3600

        horas_muelle = (
            df_filtrado["Tiempo_Muelle_Horas"]
            .clip(lower=0)
            .sum()
        )

        if horas_periodo > 0:

            ocupacion = (
                horas_muelle
                / (int(n_muelles) * horas_periodo)
                * 100
            )

    # Rendimiento descriptivo de contenedores.
    horas_contenedores = (
        contenedores["Tiempo_Muelle_Horas"]
        .clip(lower=0)
        .sum()
    )

    teus_contenedores = contenedores[
        "TEUs_Ocupados"
    ].sum(min_count=1)

    if (
        horas_contenedores > 0
        and pd.notna(teus_contenedores)
    ):

        eficiencia = (
            teus_contenedores / horas_contenedores
        )


# ============================================================
# 9. INDICADORES CLAVE
# ============================================================

st.subheader("📊 Indicadores clave de desempeño")

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Tiempo de espera promedio",
        (
            f"{espera_prom:.2f} horas"
            if pd.notna(espera_prom)
            else "N/D"
        )
    )

    st.caption(
        f"Umbral de control: {UMBRAL_CONTROL:.1f} horas"
    )

    if pd.notna(espera_prom):

        if espera_prom <= UMBRAL_CONTROL:

            st.success(
                "Promedio dentro del umbral."
            )

        else:

            st.warning(
                "Promedio superior al umbral."
            )


with c2:

    st.metric(
        "Estancia promedio en muelle",
        (
            f"{muelle_prom:.2f} horas"
            if pd.notna(muelle_prom)
            else "N/D"
        )
    )

    st.caption(
        "Promedio calculado con los tiempos de muelle válidos."
    )


with c3:

    st.metric(
        "TEUs registrados en contenedores",
        f"{teus_total:,.0f}"
    )

    st.caption(
        "Suma de los TEUs registrados en las operaciones "
        "clasificadas como contenedores."
    )


c4, c5, c6 = st.columns(3)

with c4:

    st.metric(
        "Operaciones con demora crítica",
        cant_demoras
    )

    st.caption(
        f"Espera superior a {UMBRAL_CONTROL:.1f} horas."
    )


with c5:

    st.metric(
        "Utilización teórica estimada de muelles",
        (
            f"{ocupacion:.1f}%"
            if ocupacion is not None
            else "N/D"
        )
    )

    st.caption(
        f"Estimación con {int(n_muelles)} muelles supuestos. "
        "No representa la ocupación simultánea real."
    )


with c6:

    st.metric(
        "Rendimiento descriptivo de contenedores",
        (
            f"{eficiencia:.2f} TEUs/h"
            if eficiencia is not None
            else "N/D"
        )
    )

    st.caption(
        "TEUs registrados por hora de permanencia en muelle."
    )


# ============================================================
# 10. ALERTAS DE DEMORAS CRÍTICAS
# ============================================================

st.divider()

st.subheader("⚠ Alertas de demoras críticas")

if df_filtrado.empty:

    st.info(
        "No hay operaciones para los filtros seleccionados."
    )

elif cant_demoras == 0:

    st.success(
        "No hay operaciones con espera superior a "
        f"{UMBRAL_CONTROL:.1f} horas."
    )

else:

    st.warning(
        f"Se encontraron {cant_demoras} operaciones con espera "
        f"superior a {UMBRAL_CONTROL:.1f} horas."
    )

    columnas_alerta = [
        "ID_Registro",
        "Buque",
        "Tipo_Carga",
        "Tiempo_Espera_Horas",
        "Condicion_Climatica",
    ]

    tabla_demoras = df_filtrado.loc[
        df_filtrado["Tiempo_Espera_Horas"] > UMBRAL_CONTROL,
        columnas_alerta
    ].sort_values(
        "Tiempo_Espera_Horas",
        ascending=False
    )

    st.dataframe(
        tabla_demoras,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 11. GRÁFICA DE ESPERA POR TIPO DE CARGA
# ============================================================

st.divider()

st.subheader(
    "1. Tiempo de espera promedio por tipo de carga"
)

if not df_filtrado.empty:

    espera_por_carga = (
        df_filtrado.groupby(
            "Tipo_Carga",
            as_index=False
        )["Tiempo_Espera_Horas"]
        .mean()
        .dropna(
            subset=["Tiempo_Espera_Horas"]
        )
        .sort_values(
            "Tiempo_Espera_Horas",
            ascending=False
        )
    )

if not espera_por_carga.empty:

    fig_carga = px.bar(
        espera_por_carga,
        x="Tipo_Carga",
        y="Tiempo_Espera_Horas",
        color="Tipo_Carga",
        color_discrete_map=COLORES_CARGA,
        labels={
            "Tipo_Carga": "Tipo de carga",
            "Tiempo_Espera_Horas": "Espera promedio (horas)",
        },
        text_auto=".2f",
    )

    fig_carga.add_hline(
        y=UMBRAL_CONTROL,
        line_dash="dash",
        line_color="red",
        annotation_text=(
            f"Umbral de {UMBRAL_CONTROL:.1f} horas"
        )
    )

    fig_carga.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_carga,
        use_container_width=True
    )

else:

    st.info(
        "No hay tiempos de espera válidos para esta gráfica."
    )


# ============================================================
# 12. GRÁFICA DE OPERACIONES POR TIPO DE CARGA
# ============================================================

st.subheader(
    "2. Distribución de operaciones por tipo de carga"
)

if not df_filtrado.empty:

    operaciones_carga = (
        df_filtrado["Tipo_Carga"]
        .value_counts()
        .rename_axis("Tipo_Carga")
        .reset_index(name="Cantidad")
    )

    fig_distribucion = px.pie(
        operaciones_carga,
        names="Tipo_Carga",
        values="Cantidad",
        color="Tipo_Carga",
        color_discrete_map=COLORES_CARGA,
        title="Cantidad de operaciones por tipo de carga",
        hole=0.35,
    )

    fig_distribucion.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    st.plotly_chart(
        fig_distribucion,
        use_container_width=True
    )

else:

    st.info(
        "No hay datos para mostrar esta gráfica."
    )


# ============================================================
# 13. GRÁFICA DE LLEGADAS POR HORA
# ============================================================

st.divider()

st.subheader(
    "3. Llegadas por hora del día"
)

llegadas = df_filtrado.dropna(
    subset=["Hora_Llegada"]
)

if not llegadas.empty:

    conteo_horas = llegadas.groupby(
        "Hora_del_Dia"
    ).size()

    llegadas_por_hora["Cantidad"] = (
        llegadas_por_hora["Hora_del_Dia"]
        .map(conteo_horas)
        .fillna(0)
        .astype(int)
    )

    fig_horas = px.line(
        llegadas_por_hora,
        x="Hora_del_Dia",
        y="Cantidad",
        markers=True,
        labels={
            "Hora_del_Dia": "Hora del día",
            "Cantidad": "Número de llegadas",
        },
    )

    fig_horas.update_xaxes(
        tickmode="linear",
        dtick=1
    )

    st.plotly_chart(
        fig_horas,
        use_container_width=True
    )

    if llegadas_por_hora["Cantidad"].max() > 0:

        pico = llegadas_por_hora.loc[
            llegadas_por_hora["Cantidad"].idxmax()
        ]

        st.info(
            f"La hora con más llegadas registradas es "
            f"{int(pico['Hora_del_Dia']):02d}:00, "
            f"con {int(pico['Cantidad'])} llegadas."
        )

else:

    st.info(
        "No hay fechas de llegada válidas para mostrar."
    )


# ============================================================
# 14. GRÁFICA DE ESPERA SEGÚN CONDICIÓN CLIMÁTICA
# ============================================================

st.divider()

st.subheader(
    "4. Tiempo de espera promedio según condición climática"
)

if not df_filtrado.empty:

    espera_por_clima = (
        df_filtrado.groupby(
            "Condicion_Climatica"
        )["Tiempo_Espera_Horas"]
        .agg(
            Espera_Promedio="mean",
            Casos="count"
        )
        .reset_index()
        .dropna(
            subset=["Espera_Promedio"]
        )
        .sort_values(
            "Espera_Promedio",
            ascending=False
        )
    )

if not espera_por_clima.empty:

    fig_clima = px.bar(
        espera_por_clima,
        x="Condicion_Climatica",
        y="Espera_Promedio",
        color="Condicion_Climatica",
        color_discrete_map=COLORES_CLIMA,
        hover_data=["Casos"],
        labels={
            "Condicion_Climatica": "Condición climática",
            "Espera_Promedio": "Espera promedio (horas)",
        },
        text_auto=".2f",
    )

    fig_clima.add_hline(
        y=UMBRAL_CONTROL,
        line_dash="dash",
        line_color="red",
        annotation_text=(
            f"Umbral de {UMBRAL_CONTROL:.1f} horas"
        )
    )

    fig_clima.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_clima,
        use_container_width=True
    )

    resumen_casos = ", ".join(
        f"{fila.Condicion_Climatica}: {int(fila.Casos)}"
        for fila in espera_por_clima.itertuples()
    )

    st.caption(
        f"Casos con espera válida por condición: {resumen_casos}. "
        "La asociación observada no demuestra causalidad."
    )

else:

    st.info(
        "No hay tiempos de espera válidos para comparar "
        "las condiciones climáticas."
    )


# ============================================================
# 15. RESUMEN AUTOMÁTICO DEL ANÁLISIS
# ============================================================

st.divider()

st.subheader("📝 Resumen del análisis")

if df_filtrado.empty:

    st.info(
        "Selecciona al menos una opción en cada filtro "
        "para generar el resumen."
    )

else:

    st.write(
        f"Se analizaron **{len(df_filtrado)} operaciones** "
        "con los filtros actuales."
    )

    # Resumen de tiempos de espera.
    if pd.notna(espera_prom):

        st.write(
            f"- El tiempo promedio de espera es de "
            f"**{espera_prom:.2f} horas**."
        )

        st.write(
            f"- Se identificaron **{cant_demoras} operaciones** "
            f"con espera superior a {UMBRAL_CONTROL:.1f} horas."
        )

    else:

        st.write(
            "- No hay tiempos de espera válidos para calcular "
            "el promedio."
        )

    # Tipo de carga con mayor espera.
    if not espera_por_carga.empty:

        peor = espera_por_carga.iloc[0]

        st.write(
            f"- El tipo de carga con mayor espera promedio es "
            f"**{peor['Tipo_Carga']}**, con "
            f"**{peor['Tiempo_Espera_Horas']:.2f} horas**."
        )

    # Hora con más llegadas.
    if llegadas_por_hora["Cantidad"].max() > 0:

        pico = llegadas_por_hora.loc[
            llegadas_por_hora["Cantidad"].idxmax()
        ]

        st.write(
            f"- La hora con más llegadas es "
            f"**{int(pico['Hora_del_Dia']):02d}:00**, "
            f"con **{int(pico['Cantidad'])} llegadas**."
        )

    # Condición climática con mayor espera.
    if not espera_por_clima.empty:

        clima_top = espera_por_clima.iloc[0]

        st.write(
            f"- La condición climática con mayor espera promedio "
            f"es **{clima_top['Condicion_Climatica']}**, con "
            f"**{clima_top['Espera_Promedio']:.2f} horas** "
            f"en {int(clima_top['Casos'])} casos."
        )

        st.caption(
            "Este resultado es descriptivo. No demuestra que "
            "la condición climática sea la causa de la demora."
        )

    # Ocupación teórica.
    if ocupacion is not None:

        st.write(
            f"- La utilización teórica estimada de muelles es "
            f"**{ocupacion:.1f}%**, suponiendo "
            f"{int(n_muelles)} muelles disponibles."
        )

        st.caption(
            "Esta cifra no representa la ocupación simultánea "
            "real de los muelles."
        )

    # Rendimiento descriptivo.
    if eficiencia is not None:

        st.write(
            f"- El rendimiento descriptivo de contenedores es "
            f"**{eficiencia:.2f} TEUs por hora de permanencia "
            "en muelle**."
        )

    # Recomendaciones.
    st.markdown(
        "**Recomendaciones sugeridas a partir de los datos:**"
    )

    st.markdown(
        """
        - Revisar las operaciones con tiempos de espera elevados.
        - Analizar los tipos de carga con mayores promedios de espera.
        - Evaluar las horas de mayor llegada de buques para planificar
          los recursos disponibles.
        - Comparar los tiempos de espera según la condición climática
          sin asumir una relación causal.
        - Revisar los registros ausentes, duplicados o inválidos
          antes de tomar decisiones operativas.
        """
    )


# ============================================================
# 16. PIE DE PÁGINA
# ============================================================

st.divider()

st.caption(
    "PortAnalytics | Proyecto académico de Ciencia de Datos I"
)