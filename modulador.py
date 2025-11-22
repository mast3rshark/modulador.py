# app_clean.py — Versión sin PDF y sin matplotlib
import streamlit as st
import pandas as pd
import numpy as np

# ----------------------
# UTILIDADES MUSICALES
# ----------------------
SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

CIRCLE_QUINTS = [
    'C','G','D','A','E','B','F#','C#','Gb','Db','Ab','Eb','Bb','F'
]

MAJOR_STEPS = [2,2,1,2,2,2,1]
MINOR_STEPS = [2,1,2,2,1,2,2]

def note_to_index(n):
    n = n.replace('♯','#').replace('♭','b')
    if n in SHARP: return SHARP.index(n)
    if n in FLAT:  return FLAT.index(n)
    raise ValueError("Nota desconocida: " + n)

def index_to_note(i, prefer_flats=False):
    i = i % 12
    return FLAT[i] if prefer_flats else SHARP[i]

def prefer_flats(tonic):
    left = ['F','Bb','Eb','Ab','Db','Gb','Cb']
    if tonic in left or tonic.endswith('b'):
        return True
    return False

def build_scale(tonic, mode='major'):
    tonic = tonic.replace('♯','#').replace('♭','b')
    pf = prefer_flats(tonic)
    start = note_to_index(tonic)
    steps = MAJOR_STEPS if mode=='major' else MINOR_STEPS
    notes = [index_to_note(start, pf)]
    i = start
    for s in steps[:-1]:
        i = (i + s) % 12
        notes.append(index_to_note(i, pf))
    return notes

def triad(scale, degree):
    n = len(scale)
    return [
        scale[(degree-1) % n],
        scale[(degree+1) % n],
        scale[(degree+3) % n]
    ]

def seventh(scale, degree):
    n = len(scale)
    return [
        scale[(degree-1) % n],
        scale[(degree+1) % n],
        scale[(degree+3) % n],
        scale[(degree+5) % n]
    ]

# ----------------------
# STREAMLIT UI
# ----------------------
st.set_page_config(page_title="Armonía Interactiva", layout="wide")
st.title("🎵 Armonía Interactiva — Basado en 'Armonía Ilustrada'")

page = st.sidebar.selectbox(
    "Navegar",
    ["Círculo de Quintas", "Modos y Acordes", "Modulación interactiva", "Conceptos del Libro"]
)

# ----------------------
# CÍRCULO DE QUINTAS (texto)
# ----------------------
if page == "Círculo de Quintas":
    st.header("Círculo de Quintas — Versión ligera")
    st.write("""
El círculo de quintas muestra cómo las tonalidades están relacionadas entre sí.
Hacia la derecha hay más sostenidos (#), hacia la izquierda más bemoles (b).
""")

    tonic = st.selectbox("Escoge una tonalidad", CIRCLE_QUINTS)

    idx = CIRCLE_QUINTS.index(tonic)
    right = CIRCLE_QUINTS[(idx+1)%len(CIRCLE_QUINTS)]
    left = CIRCLE_QUINTS[(idx-1)%len(CIRCLE_QUINTS)]

    st.subheader("Vecinos")
    st.write(f"→ A la derecha (más #): **{right}**")
    st.write(f"← A la izquierda (más b): **{left}**")

    st.subheader("Moverse a otra tonalidad")
    target = st.selectbox("Destino", CIRCLE_QUINTS)

    dist = CIRCLE_QUINTS.index(target) - idx

    st.write(f"Distancia en el círculo: **{dist} pasos**")

    if abs(dist) <= 1:
        st.success("Modulación muy suave (tonalidades vecinas).")
    elif abs(dist) <= 3:
        st.info("Modulación moderada (usa acordes pivote).")
    else:
        st.warning("Modulación fuerte (usa dominantes secundarios o sustitutos tritonales).")

# ----------------------
# MODOS Y ACORDES
# ----------------------
elif page == "Modos y Acordes":
    st.header("Modos y Acordes Diatónicos")

    tonic = st.selectbox("Tónica", SHARP + FLAT)
    mode = st.radio("Modo", ["major", "minor"])

    scale = build_scale(tonic, mode)

    st.subheader("Escala")
    st.write(scale)

    st.subheader("Acordes en el modo")
    degrees = ["I","ii","iii","IV","V","vi","vii°"]
    data = []

    for i, deg in enumerate(degrees, start=1):
        data.append({
            "Grado": deg,
            "Triada": " - ".join(triad(scale, i)),
            "Séptima": " - ".join(seventh(scale, i)),
        })

    st.table(pd.DataFrame(data))

    st.subheader("Modos derivados (jónico → locrio)")
    # Para modos siempre usamos la escala mayor relativa
    major_scale = build_scale(
        tonic if mode=="major" else index_to_note((note_to_index(tonic)+3)%12),
        "major"
    )

    mode_names = ["Jónico","Dórico","Frigio","Lidio","Mixolidio","Eólico","Locrio"]

    for i, name in enumerate(mode_names):
        m = [major_scale[(i+j)%7] for j in range(7)]
        st.write(f"**{name}** → {', '.join(m)}")

# ----------------------
# MODULACIÓN
# ----------------------
elif page == "Modulación interactiva":
    st.header("Herramienta de Modulación")

    origin = st.selectbox("Tonalidad origen", CIRCLE_QUINTS)
    target = st.selectbox("Tonalidad destino", CIRCLE_QUINTS)

    if st.button("Calcular"):
        st.write(f"De **{origin}** a **{target}**")

        pos_o = CIRCLE_QUINTS.index(origin)
        pos_t = CIRCLE_QUINTS.index(target)

        dist = pos_t - pos_o
        st.write(f"Distancia: **{dist} pasos**")

        if abs(dist) <= 1:
            st.success("Modulación suave: usa acordes pivote y notas comunes.")
        elif abs(dist) <= 3:
            st.info("Modulación media: dominante secundaria o subV7.")
        else:
            st.warning("Modulación fuerte: cadena de dominantes o sustituto tritonal.")

        st.write("### Sugerencias:")
        st.write("- Busca acordes comunes en ambas tonalidades")
        st.write("- Introduce el **V7** del destino")
        st.write("- Usa una nota común como pegamento melódico")

# ----------------------
# CONCEPTOS DEL LIBRO
# ----------------------
elif page == "Conceptos del Libro":
    st.header("Conceptos Clave del Libro (Texto)")

    st.subheader("Glue mágico")
    st.write("""
La melodía es el pegamento entre los acordes.  
Si mantienes una o dos notas estables, la modulación será mucho más suave.
""")

    st.subheader("Acordes pivote")
    st.write("""
Un acorde que pertenece a ambas tonalidades permite
cambiar sin sobresaltos (muy útil para modulaciones suaves).
""")

    st.subheader("Sustitutos tritonales")
    st.write("""
El V7 puede reemplazarse por bII7 (subV7), creando tensión elegante para modulaciones lejanas.
""")

    st.subheader("Cadena de dominantes")
    st.write("""
Ideal para modulaciones fuertes:  
VII7 → III7 → VI7 → II7 → V7 → I
""")
