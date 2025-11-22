# app_pdf_viewer.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

# ---------- Ruta al PDF ----------
PDF_PATH = "/mnt/data/Brian Callipari - Armonía Ilustrada - Español.pdf"

# ---------- Utiles musicales ----------
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
    right = ['G','D','A','E','B','F#','C#']
    if tonic in left or tonic.endswith('b'): return True
    if tonic in right or tonic.endswith('#'): return False
    return False

def build_scale(tonic, mode='major'):
    tonic = tonic.replace('♯','#').replace('♭','b')
    pf = prefer_flats(tonic)
    start = note_to_index(tonic)
    steps = MAJOR_STEPS if mode=='major' else MINOR_STEPS
    notes = [index_to_note(start, pf)]
    idx = start
    for s in steps[:-1]:
        idx = (idx + s) % 12
        notes.append(index_to_note(idx, pf))
    return notes

def triad(scale, degree):
    n = len(scale)
    return [ scale[(degree-1) % n], scale[(degree+1) % n], scale[(degree+3) % n] ]

def seventh(scale, degree):
    n = len(scale)
    return [ scale[(degree-1) % n], scale[(degree+1) % n], scale[(degree+3) % n], scale[(degree+5) % n] ]

# ---------- UI ----------
st.set_page_config(page_title="Armonía Ilustrada — Interactivo", layout="wide")
st.title("📘 Armonía Ilustrada — Interactivo")
st.write("Explora conceptos del libro de forma interactiva: círculo de quintas, modos, acordes y modulaciones.")

# Sidebar
st.sidebar.header("Navegación")
page = st.sidebar.selectbox(
    "Ir a",
    ["Índice & PDF", "Círculo de Quintas", "Modos y Acordes", "Modulación interactiva", "Notas del autor / Glue"]
)
st.sidebar.markdown(f"[📄 Abrir PDF completo]({PDF_PATH})")

# ------------------ INDEX PAGE ------------------
if page == "Índice & PDF":
    st.header("Índice rápido del PDF")
    st.write("""
    - Escalas mayores y menores  
    - Dominantes  
    - Disminuidos  
    - Aumentados  
    - Puentes  
    - Sustitutos tritonales  
    - Modulación  
    - Proximidad de acordes  
    """)

    st.subheader("Visualizador del PDF")
    try:
        st.markdown(
            f"<iframe src='{PDF_PATH}' width='100%' height='600'></iframe>",
            unsafe_allow_html=True
        )
    except:
        st.warning("Si no se carga, usa el link de la barra lateral.")

# ------------------ CIRCLE OF FIFTHS ------------------
elif page == "Círculo de Quintas":
    st.header("Círculo de Quintas — Interactivo")

    fig, ax = plt.subplots(figsize=(6, 6))
    labels = CIRCLE_QUINTS
    n = len(labels)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)
    xs = np.cos(angles)
    ys = np.sin(angles)

    ax.scatter(xs, ys)

    for i, lab in enumerate(labels):
        ax.text(xs[i]*1.12, ys[i]*1.12, lab, ha='center', fontsize=12)

    ax.add_artist(plt.Circle((0,0), 1.0, fill=False, linestyle="--"))
    ax.set_xticks([]); ax.set_yticks([])
    st.pyplot(fig)

    tonic = st.selectbox("Escoge tónica", labels)
    idx = labels.index(tonic)
    right = labels[(idx+1)%n]
    left = labels[(idx-1)%n]

    st.write(f"Vecino derecho (más #): **{right}**")
    st.write(f"Vecino izquierdo (más b): **{left}**")

    target = st.selectbox("Destino", labels)
    steps = labels.index(target) - idx

    st.write(f"Distancia: {steps} pasos (positivo = horario). Recomendación: 0 = mismo tono; ±1 = suave; ±2-3 = moderada; ≥4 = fuerte.")

# ------------------ MODES & CHORDS ------------------
elif page == "Modos y Acordes":
    st.header("Modos y acordes diatónicos")

    tonic = st.selectbox("Tónica", SHARP + FLAT)
    mode_base = st.radio("Modo", ["major", "minor"])

    scale = build_scale(tonic, mode_base)
    st.subheader("Escala")
    st.write(scale)

    st.subheader("Acordes del modo (triada y séptima)")
    degrees = ["I","ii","iii","IV","V","vi","vii°"]
    rows = []
    for i, deg in enumerate(degrees, start=1):
        rows.append({
            "Grado": deg,
            "Triada": " - ".join(triad(scale, i)),
            "7ma": " - ".join(seventh(scale, i))
        })

    df = pd.DataFrame(rows)
    st.table(df)

    st.subheader("Modos derivados (jónico → locrio)")

    major_scale = build_scale(
        tonic if mode_base=="major" else index_to_note((note_to_index(tonic)+3)%12),
        "major"
    )

    mode_names = ["Jónico","Dórico","Frigio","Lidio","Mixolidio","Eólico","Locrio"]

    for i in range(7):
        mode_notes = [major_scale[(i+j) % 7] for j in range(7)]
        st.write(f"**{mode_names[i]}** → {', '.join(mode_notes)}")

# ------------------ MODULATION TOOL ------------------
elif page == "Modulación interactiva":
    st.header("Herramienta de modulación")

    origin = st.selectbox("Tonalidad origen", CIRCLE_QUINTS)
    target = st.selectbox("Tonalidad destino", CIRCLE_QUINTS)

    if st.button("Calcular modulación"):
        st.write(f"De **{origin}** → **{target}**")

        pos_o = CIRCLE_QUINTS.index(origin)
        pos_t = CIRCLE_QUINTS.index(target)
        dist = pos_t - pos_o

        st.write(f"Distancia: {dist} pasos (positivo = horario). Recomendación: 0 = mismo tono; ±1 = muy suave; ±2-3 = moderada; ≥4 = fuerte.")

        if abs(dist) <= 1:
            st.success("Modulación suave: usa acordes pivote y notas comunes.")
        elif abs(dist) <= 3:
            st.info("Modulación media: dominante secundaria o cadencia intermedia.")
        else:
            st.warning("Modulación lejana: usa sustituto tritonal o cadena de dominantes.")

        st.subheader("Sugerencias generales:")
        st.write("- Busca acordes comunes entre ambas tonalidades.")
        st.write("- Introduce el V7 de la tonalidad destino.")
        st.write("- Mantén una nota común como “pegamento melódico”.")

# ------------------ GLUE ------------------
elif page == "Notas del autor / Glue":
    st.header("Glue mágico — Notas del libro")
    st.write("""
    • La melodía actúa como pegamento entre los acordes  
    • Mantener una o dos notas estables ayuda a suavizar la modulación  
    • El acorde pivote funciona cuando pertenece a ambas tonalidades  
    """)
