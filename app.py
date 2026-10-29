
# ============================================================
# PORTANALYTICS - DASHBOARD DE ANALITICA LOGISTICA PORTUARIA
# ============================================================

from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# ============================================================
# 1. CONFIGURACION GENERAL
# ============================================================

st.set_page_config(
    page_title="PortAnalytics",
    page_icon="⚓",
    layout="wide"
)

UMBRAL_CONTROL = 3.0
ARCHIVO_CSV = (
    Path(__file__).resolve().parent
    / "datos_logisticos_limpios.csv"
)


# ============================================================
# 2. CARGA Y VALIDACION DE LOS DATOS
# ============================================================

@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos(ruta_archivo):

    df = pd.read_csv(ruta_archivo)

    columnas_requeridas = [
        "ID_Registro",
        "Buque",
        "Tipo_Carga",
        "Hora_Llegada",
        "Tiempo_Espera_Horas",
        "Tiempo_Muelle_Horas",
        "TEUs_Ocupados",
        "Condicion_Climatica"
    ]

    faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas en el CSV: "
            + ", ".join(faltantes)
        )

    # Convertir la llegada a fecha y hora.
    df["Hora_Llegada"] = pd.to_datetime(
        df["Hora_Llegada"],
        errors="coerce"
    )

    # Convertir los indicadores a valores numericos.
    columnas_numericas = [
        "Tiempo_Espera_Horas",
        "Tiempo_Muelle_Horas",
        "TEUs_Ocupados"
    ]

    for columna in columnas_numericas:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        )

    # Limpiar los espacios de los campos de texto.
    columnas_texto = [
        "ID_Registro",
        "Buque",
        "Tipo_Carga",
        "Condicion_Climatica"
    ]

    for columna in columnas_texto:
        df[columna] = (
            df[columna]
            .fillna("Sin dato")
            .astype(str)
            .str.strip()
            .replace("", "Sin dato")
        )

    # La hora permite estudiar las llegadas por horario.
    df["Hora_del_Dia"] = (
        df["Hora_Llegada"].dt.hour
    )

    return df


# ============================================================
# 3. TITULO Y DESCRIPCION
# ============================================================

st.title("⚓ PortAnalytics")
st.subheader(
    "Dashboard de analitica logistica portuaria"
)

st.markdown(
    """
    Herramienta para explorar las operaciones portuarias,
    analizar tiempos de espera, revisar el tiempo en muelle
    e identificar posibles demoras.
    """
)

st.divider()


# ============================================================
# 4. CARGAR ARCHIVO
# ============================================================

try:
    df = cargar_datos(ARCHIVO_CSV)

except FileNotFoundError:
    st.error(
        "No se encontro el archivo "
        "'datos_logisticos_limpios.csv'. "
        "Verifica que este en la misma carpeta que app.py."
    )
    st.stop()

except Exception as error:
    st.error(
        f"No fue posible cargar los datos: {error}"
    )
    st.stop()


# ============================================================
# 5. FILTROS LATERALES
# ============================================================

st.sidebar.header("Filtros de operaciones")

tipos_carga = sorted(
    df["Tipo_Carga"].dropna().unique().tolist()
)

buques = sorted(
    df["Buque"].dropna().unique().tolist()
)

climas = sorted(
    df["Condicion_Climatica"].dropna().unique().tolist()
)

cargas_seleccionadas = st.sidebar.multiselect(
    "Tipo de carga",
    options=tipos_carga,
    default=tipos_carga
)

buques_seleccionados = st.sidebar.multiselect(
    "Buque",
    options=buques,
    default=buques
)

climas_seleccionados = st.sidebar.multiselect(
    "Condicion climatica",
    options=climas,
    default=climas
)

n_muelles = st.sidebar.number_input(
    "Numero supuesto de muelles",
    min_value=1,
    max_value=100,
    value=5,
    step=1
)

st.sidebar.caption(
    "La ocupacion es estimada y depende del numero "
    "de muelles indicado."
)

if st.sidebar.button(
    "Restablecer filtros",
    use_container_width=True
):
    st.cache_data.clear()
    st.rerun()


# ============================================================
# 6. APLICAR FILTROS
# ============================================================

df_filtrado = df[
    df["Tipo_Carga"].isin(cargas_seleccionadas)
    & df["Buque"].isin(buques_seleccionados)
    & df["Condicion_Climatica"].isin(
        climas_seleccionados
    )
].copy()

st.caption(
    f"Registros seleccionados: {len(df_filtrado)} "
    f"de {len(df)}"
)


# ============================================================
# 7. CALCULO DE LOS SEIS INDICADORES
# ============================================================

if not df_filtrado.empty:

    # Indicador 1: tiempo promedio de espera.
    espera_prom = (
        df_filtrado["Tiempo_Espera_Horas"].mean()
    )

    # Indicador 2: tiempo promedio en muelle.
    muelle_prom = (
        df_filtrado["Tiempo_Muelle_Horas"].mean()
    )

    # Indicador 3: total de TEUs registrados.
    teus_total = (
        df_filtrado["TEUs_Ocupados"].sum()
    )

    # Indicador 4: operaciones con espera superior
    # al umbral de control.
    cant_demoras = int(
        (
            df_filtrado["Tiempo_Espera_Horas"]
            > UMBRAL_CONTROL
        ).sum()
    )

    # Indicador 5: ocupacion estimada de los muelles.
    # Se usa el periodo completo del archivo y el
    # numero de muelles indicado en el filtro lateral.
    llegadas_validas = (
        df["Hora_Llegada"].dropna()
    )

    if (
        len(llegadas_validas) >= 2
        and n_muelles > 0
    ):

        horas_periodo = (
            llegadas_validas.max()
            - llegadas_validas.min()
        ).total_seconds() / 3600

        horas_muelle_filtradas = (
            df_filtrado["Tiempo_Muelle_Horas"]
            .clip(lower=0)
            .sum()
        )

        horas_disponibles = (
            n_muelles * horas_periodo
        )

        if horas_disponibles > 0:
            ocupacion = (
                horas_muelle_filtradas
                / horas_disponibles
            ) * 100
        else:
            ocupacion = None

    else:
        ocupacion = None

    # Indicador 6: rendimiento aproximado de
    # las operaciones de contenedores.
    contenedores = df_filtrado[
        df_filtrado["Tipo_Carga"] == "Contenedores"
    ]

    horas_contenedores = (
        contenedores["Tiempo_Muelle_Horas"]
        .clip(lower=0)
        .sum()
    )

    teus_contenedores = (
        contenedores["TEUs_Ocupados"].sum()
    )

    if horas_contenedores > 0:
        eficiencia = (
            teus_contenedores
            / horas_contenedores
        )
    else:
        eficiencia = None

else:
    espera_prom = None
    muelle_prom = None
    teus_total = 0
    cant_demoras = 0
    ocupacion = None
    eficiencia = None


# ============================================================
# 8. PRESENTACION DE LOS SEIS INDICADORES
# ============================================================

st.subheader("Indicadores clave de desempeño")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Tiempo de espera promedio",
        (
            f"{espera_prom:.1f} h"
            if pd.notna(espera_prom)
            else "N/D"
        )
    )

with c2:
    st.metric(
        "Estancia promedio en muelle",
        (
            f"{muelle_prom:.1f} h"
            if pd.notna(muelle_prom)
            else "N/D"
        )
    )

with c3:
    st.metric(
        "TEUs registrados",
        f"{teus_total:,.0f}"
    )

c4, c5, c6 = st.columns(3)

with c4:
    st.metric(
        "Casos con demora",
        cant_demoras
    )

with c5:
    st.metric(
        "Ocupacion estimada de muelles",
        (
            f"{ocupacion:.1f}%"
            if ocupacion is not None
            else "N/D"
        )
    )

with c6:
    st.metric(
        "Rendimiento de contenedores",
        (
            f"{eficiencia:.1f} TEUs/h"
            if eficiencia is not None
            else "N/D"
        )
    )

st.caption(
    "Nota: la ocupacion es una estimacion basada en "
    "el numero supuesto de muelles y el periodo del "
    "archivo. El rendimiento expresa TEUs registrados "
    "por hora de permanencia en muelle."
)


# ============================================================
# 9. ALERTAS DE DEMORAS
# ============================================================

st.subheader("Alertas de operaciones")

if df_filtrado.empty:

    st.info(
        "No hay operaciones para los filtros seleccionados."
    )

elif cant_demoras == 0:

    st.success(
        "No se encontraron operaciones con espera "
        f"superior a {UMBRAL_CONTROL:.1f} horas."
    )

else:

    st.warning(
        f"Se encontraron {cant_demoras} operaciones "
        f"con espera superior a "
        f"{UMBRAL_CONTROL:.1f} horas."
    )

    tabla_demoras = df_filtrado[
        df_filtrado["Tiempo_Espera_Horas"]
        > UMBRAL_CONTROL
    ].copy()

    tabla_demoras = tabla_demoras.sort_values(
        "Tiempo_Espera_Horas",
        ascending=False
    )

    columnas_alerta = [
        "ID_Registro",
        "Buque",
        "Tipo_Carga",
        "Tiempo_Espera_Horas",
        "Condicion_Climatica"
    ]

    st.dataframe(
        tabla_demoras[columnas_alerta],
        width="stretch",
        hide_index=True
    )


# ============================================================
# 10. GRAFICO: ESPERA PROMEDIO POR TIPO DE CARGA
# ============================================================

st.divider()
st.subheader("Analisis por tipo de carga")

if not df_filtrado.empty:

    espera_por_carga = (
        df_filtrado
        .groupby("Tipo_Carga", as_index=False)
        ["Tiempo_Espera_Horas"]
        .mean()
        .sort_values(
            "Tiempo_Espera_Horas",
            ascending=False
        )
    )

    figura_carga = px.bar(
        espera_por_carga,
        x="Tipo_Carga",
        y="Tiempo_Espera_Horas",
        title="Tiempo promedio de espera por tipo de carga",
        labels={
            "Tipo_Carga": "Tipo de carga",
            "Tiempo_Espera_Horas": "Espera promedio (horas)"
        },
        text_auto=".2f"
    )

    figura_carga.update_layout(
        xaxis_title="Tipo de carga",
        yaxis_title="Horas de espera",
        xaxis_tickangle=-20
    )

    st.plotly_chart(
        figura_carga,
        width="stretch"
    )

else:
    st.info(
        "No hay datos para mostrar este grafico."
    )


# ============================================================
# 11. GRAFICO: CANTIDAD DE OPERACIONES POR CARGA
# ============================================================

st.subheader("Distribucion de las operaciones")

if not df_filtrado.empty:

    operaciones_por_carga = (
        df_filtrado["Tipo_Carga"]
        .value_counts()
        .rename_axis("Tipo_Carga")
        .reset_index(name="Cantidad")
    )

    figura_distribucion = px.pie(
        operaciones_por_carga,
        names="Tipo_Carga",
        values="Cantidad",
        title="Cantidad de operaciones por tipo de carga",
        hole=0.35
    )

    figura_distribucion.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    st.plotly_chart(
        figura_distribucion,
        width="stretch"
    )

else:
    st.info(
        "No hay datos para mostrar este grafico."
    )


# ============================================================
# 12. GRAFICO: LLEGADAS POR HORA DEL DIA
# ============================================================

st.divider()
st.subheader("Patrones de llegada de los buques")

llegadas = df_filtrado.dropna(
    subset=["Hora_Llegada"]
).copy()

if not llegadas.empty:

    llegadas["Hora_del_Dia"] = (
        llegadas["Hora_Llegada"].dt.hour
    )

    llegadas_por_hora = (
        llegadas
        .groupby("Hora_del_Dia")
        .size()
        .reindex(range(24), fill_value=0)
        .rename("Cantidad")
        .reset_index()
    )

    figura_horas = px.line(
        llegadas_por_hora,
        x="Hora_del_Dia",
        y="Cantidad",
        markers=True,
        title="Cantidad de llegadas por hora del dia",
        labels={
            "Hora_del_Dia": "Hora del dia",
            "Cantidad": "Numero de llegadas"
        }
    )

    figura_horas.update_xaxes(
        tickmode="linear",
        dtick=1
    )

    st.plotly_chart(
        figura_horas,
        width="stretch"
    )

else:
    st.info(
        "No hay horas de llegada validas para mostrar."
    )


# ============================================================
# 13. GRAFICO: ESPERA PROMEDIO POR CLIMA
# ============================================================

st.subheader("Influencia observada de las condiciones climaticas")

if not df_filtrado.empty:

    espera_por_clima = (
        df_filtrado
        .groupby("Condicion_Climatica", as_index=False)
        ["Tiempo_Espera_Horas"]
        .mean()
        .sort_values(
            "Tiempo_Espera_Horas",
            ascending=False
        )
    )

    figura_clima = px.bar(
        espera_por_clima,
        x="Condicion_Climatica",
        y="Tiempo_Espera_Horas",
        title="Tiempo promedio de espera por condicion climatica",
        labels={
            "Condicion_Climatica": "Condicion climatica",
            "Tiempo_Espera_Horas": "Espera promedio (horas)"
        },
        text_auto=".2f"
    )

    figura_clima.update_layout(
        xaxis_tickangle=-20
    )

    st.plotly_chart(
        figura_clima,
        width="stretch"
    )

else:
    st.info(
        "No hay datos para mostrar este grafico."
    )


# ============================================================
# 14. CONCLUSIONES AUTOMATICAS
# ============================================================

st.divider()
st.subheader("Resumen del analisis")

if df_filtrado.empty:

    st.info(
        "Selecciona operaciones en los filtros para "
        "generar el resumen."
    )

else:

    st.write(
        f"Se analizaron **{len(df_filtrado)} operaciones** "
        "con los filtros actuales."
    )

    if pd.notna(espera_prom):

        st.write(
            f"El tiempo promedio de espera es de "
            f"**{espera_prom:.2f} horas**."
        )

    if pd.notna(muelle_prom):

        st.write(
            f"El tiempo promedio de permanencia en muelle "
            f"es de **{muelle_prom:.2f} horas**."
        )

    st.write(
        f"Se identificaron **{cant_demoras} operaciones** "
        f"con espera superior a {UMBRAL_CONTROL:.1f} horas."
    )

    if cant_demoras > 0:

        st.write(
            "Se recomienda revisar estas operaciones para "
            "identificar posibles causas de espera prolongada."
        )

    if ocupacion is not None:

        st.write(
            f"La ocupacion estimada bajo el supuesto de "
            f"{n_muelles} muelles es de **{ocupacion:.1f}%**. "
            "Este resultado no representa una medicion real "
            "de ocupacion simultanea."
        )

    if eficiencia is not None:

        st.write(
            f"El rendimiento calculado para las operaciones "
            f"de contenedores es de **{eficiencia:.1f} TEUs "
            "por hora de permanencia en muelle**."
        )

st.caption(
    "PortAnalytics | Proyecto academico de Ciencias de Datos I"
)
