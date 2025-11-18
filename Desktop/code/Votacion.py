# Requiere: pip install streamlit-autorefresh
import streamlit as st
import pandas as pd
import os
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
