# Requiere: pip install streamlit-autorefresh altair
import streamlit as st
import pandas as pd
import os
import time
import json
import altair as alt
from streamlit_autorefresh import st_autorefresh

# Configuración
EQUIPOS = [
    "Maria Elvira",
    "Pau, Pauli, Carmen",
    "Anna, Oria, Carla",
    "Pablo, Alejandra",
    "Javi, Jorge",
    "Manu, Tomas, Paula",
    "Dario, Mateo",
    "Mariana, Ainhora, Sara"
]
CATEGORIAS = ["sabor", "presentacion", "creatividad"]
ARCHIVO_VOTOS = "votos.csv"

# Crear archivo si no existe
if not os.path.exists(ARCHIVO_VOTOS):
    pd.DataFrame(columns=["votante", "evaluado", "categoria", "puntos"]).to_csv(ARCHIVO_VOTOS, index=False)

# Autorefresh: reejecuta el script cada 1 segundo (1000 ms)
count = st_autorefresh(interval=1000, key="votos_autorefresh")

st.set_page_config(page_title="Cena por comunidades", layout="centered")
st.title("🍽️ Cena por comunidades")

# CSS para ocultar el icono humano / toolbar superior
st.markdown(
    """
    <style>
    /* Oculta la toolbar superior completa (incluye el icono de usuario) */
    [data-testid="stToolbar"] {display: none !important;}

    /* Si alguna parte queda visible en versiones futuras, también intentamos ocultar el avatar específico */
    button[aria-label="Open user menu"], img[alt="Avatar"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True
)

# Selección del votante
equipo_votante = st.selectbox("¿Quién está votando?", EQUIPOS)

# Cargar votos actuales (se lee siempre en cada ejecución)
df_votos = pd.read_csv(ARCHIVO_VOTOS)

# Sección de votación
st.subheader("🗳️ Evalúa a los otros equipos")
for evaluado in EQUIPOS:
    if evaluado == equipo_votante:
        continue

    ya_voto = (
        df_votos[(df_votos["votante"] == equipo_votante) & (df_votos["evaluado"] == evaluado)]
        .shape[0] >= len(CATEGORIAS)
    )

    with st.expander(f"Votar a {evaluado}"):
        if ya_voto:
            st.info("✅ Ya has votado a este equipo.")
        else:
            puntos = {}
            for cat in CATEGORIAS:
                puntos[cat] = st.slider(
                    f"{cat.title()} para {evaluado}", 0, 10, 5,
                    key=f"{equipo_votante}_{evaluado}_{cat}"
                )
            if st.button(f"Registrar voto para {evaluado}", key=f"btn_{equipo_votante}_{evaluado}"):
                # Leer de nuevo por si hubo cambios entre abrir y guardar
                df_votos = pd.read_csv(ARCHIVO_VOTOS)
                for cat in CATEGORIAS:
                    nuevo_voto = pd.DataFrame([{
                        "votante": equipo_votante,
                        "evaluado": evaluado,
                        "categoria": cat,
                        "puntos": puntos[cat]
                    }])
                    df_votos = pd.concat([df_votos, nuevo_voto], ignore_index=True)
                df_votos.to_csv(ARCHIVO_VOTOS, index=False)
                st.success(f"✅ Voto registrado para {evaluado}")
                st.experimental_rerun()

# Sección de resultados en tiempo real
st.subheader("📊 Resultados en tiempo real")
if not df_votos.empty:
    resumen = df_votos.groupby(["evaluado", "categoria"])["puntos"].mean().unstack().fillna(0)
    resumen["Media Total"] = resumen.mean(axis=1)
    resumen = resumen.reset_index().rename(columns={"evaluado": "Equipo"})
    st.dataframe(resumen.style.format(precision=2))

    if resumen["Media Total"].max() > 0:
        ganadores = resumen[resumen["Media Total"] == resumen["Media Total"].max()]
        nombres = ", ".join(ganadores["Equipo"])
        st.markdown(f"### 🏆 Ganador: {nombres} — media {ganadores['Media Total'].iloc[0]:.2f}")
else:
    st.info("Aún no hay votos registrados.")

# === Estadísticas y gráficos adicionales ===
st.markdown("---")
st.subheader("📈 Estadísticas y gráficos")

# Asegurar df_votos actualizado
df_votos = pd.read_csv(ARCHIVO_VOTOS)

if df_votos.empty:
    st.info("No hay datos para mostrar estadísticas.")
else:
    # Estadísticas globales
    total_votos = len(df_votos)
    total_votantes = df_votos["votante"].nunique()
    total_evaluados = df_votos["evaluado"].nunique()
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total filas", f"{total_votos}")
    col_b.metric("Votantes únicos", f"{total_votantes}")
    col_c.metric("Equipos evaluados", f"{total_evaluados}")

    # Tabla resumen por equipo (media por categoría y total)
    resumen = df_votos.groupby(["evaluado", "categoria"])["puntos"].mean().unstack().fillna(0)
    resumen["Media Total"] = resumen.mean(axis=1)
    resumen = resumen.reset_index().rename(columns={"evaluado": "Equipo"})
    st.write("**Resumen por equipo (medias)**")
    st.dataframe(resumen.style.format(precision=2), height=300)

    # Gráfico 1: barras horizontales de Media Total por equipo
    barra_total = alt.Chart(resumen).mark_bar().encode(
        x=alt.X("Media Total:Q", title="Media total"),
        y=alt.Y("Equipo:N", sort='-x'),
        color=alt.Color("Media Total:Q", scale=alt.Scale(scheme='blues')),
        tooltip=[alt.Tooltip("Equipo:N"), alt.Tooltip("Media Total:Q", format=".2f")]
    ).properties(height=300)
    st.altair_chart(barra_total, use_container_width=True)

    # Gráfico 2: perfil por equipo (líneas por categoría)
    df_largo = df_votos.groupby(["evaluado", "categoria"])["puntos"].mean().reset_index().rename(columns={"evaluado":"Equipo"})
    line_chart = alt.Chart(df_largo).mark_line(point=True).encode(
        x=alt.X("categoria:N", title="Categoría"),
        y=alt.Y("puntos:Q", title="Puntuación media", scale=alt.Scale(domain=[0,10])),
        color=alt.Color("Equipo:N"),
        tooltip=["Equipo", "categoria", alt.Tooltip("puntos:Q", format=".2f")]
    ).properties(height=320)
    st.write("**Perfil por equipo (por categoría)**")
    st.altair_chart(line_chart, use_container_width=True)

    # Gráficos de columnas por categoría (puntuación media de cada equipo)
    st.write("**Puntuación media por equipo en cada categoría**")
    media_por_equipo_cat = df_votos.groupby(["evaluado", "categoria"])["puntos"].mean().reset_index().rename(columns={"evaluado": "Equipo", "puntos": "Media"})

    cols = st.columns(len(CATEGORIAS))
    for idx, cat in enumerate(CATEGORIAS):
        with cols[idx]:
            df_cat = media_por_equipo_cat[media_por_equipo_cat["categoria"] == cat].copy()
            if df_cat.empty:
                st.write(f"{cat.title()}: sin datos")
            else:
                # Ordenar equipos por media descendente para mejor lectura
                df_cat = df_cat.sort_values("Media", ascending=False)
                bars = alt.Chart(df_cat).mark_bar().encode(
                    x=alt.X("Media:Q", title="Puntuación media", scale=alt.Scale(domain=[0,10])),
                    y=alt.Y("Equipo:N", sort=alt.EncodingSortField(field="Media", op="mean", order="descending")),
                    color=alt.Color("Media:Q", scale=alt.Scale(scheme='tealblue')),
                    tooltip=[alt.Tooltip("Equipo:N"), alt.Tooltip("Media:Q", format=".2f")]
                ).properties(title=cat.title(), height=320)
                st.altair_chart(bars, use_container_width=True)

    # Gráficos circulares por categoría (porcentaje según media de puntuación)
    st.write("**Gráficos circulares por categoría (porcentaje según media de puntuación)**")
    pie_cols = st.columns(len(CATEGORIAS))
    for i, cat in enumerate(CATEGORIAS):
        with pie_cols[i]:
            df_pie = media_por_equipo_cat[media_por_equipo_cat["categoria"] == cat].copy()
            if df_pie.empty:
                st.write(f"{cat.title()}: sin datos")
                continue
            pie = alt.Chart(df_pie).mark_arc(innerRadius=30).encode(
                theta=alt.Theta(field="Media", type="quantitative"),
                color=alt.Color(field="Equipo", type="nominal"),
                tooltip=[alt.Tooltip("Equipo:N"), alt.Tooltip("Media:Q", format=".2f")]
            ).properties(height=300, title=cat.title())
            total_media = df_pie["Media"].sum()
            st.altair_chart(pie, use_container_width=True)
            st.caption(f"Suma de medias (para proporción): {total_media:.2f}")

    # Opcional: descarga de CSV con estadísticas agregadas
    csv_bytes = resumen.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar resumen CSV", data=csv_bytes, file_name="resumen_votos.csv", mime="text/csv")