# app_pdf_viewer.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

# ---------- Ruta al PDF (archivo que subiste) ----------
PDF_PATH = "/mnt/data/Brian Callipari - Armonía Ilustrada - Español.pdf"

# ---------- Utiles musicales (escala, acordes, modos) ----------
SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

CIRCLE_QUINTS = ['C','G','D','A','E','B','F#','C#','Gb','Db','Ab','Eb','Bb','F']  # order for visual

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
    # decide flats vs sharps by circle side (left = flats, right = sharps)
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

def triad_from_scale(scale, degree):
    n = len(scale)
    return [ scale[(degree-1) % n], scale[(degree+1) % n], scale[(degree+3) % n] ]

def seventh_from_scale(scale, degree):
    n = len(scale)
    return [ scale[(degree-1) % n], scale[(degree+1) % n], scale[(degree+3) % n], scale[(degree+5) % n] ]

# ---------- UI ----------
st.set_page_config(page_title="Armonía Ilustrada — Interactivo", layout="wide")
st.title("📘 Armonía Ilustrada — Interactivo")
st.markdown("App interactiva para explorar el contenido del PDF y experimentar conceptos: círculo de quintas, modos, acordes, modulaciones y puentes.")

# Sidebar
st.sidebar.header("Navegación")
page = st.sidebar.selectbox("Ir a", ["Índice & PDF", "Círculo de Quintas", "Modos y Acordes", "Modulación interactiva", "Notas del autor / Glue mágico"])
st.sidebar.markdown("---")
st.sidebar.markdown(f"[Abrir PDF completo]({PDF_PATH})")
st.sidebar.caption("Ruta del archivo subido (local):\n`/mnt/data/Brian Callipari - Armonía Ilustrada - Español.pdf`")

# ------------------ INDEX & PDF ------------------
if page == "Índice & PDF":
    st.header("Índice y vista rápida del PDF")
    st.markdown("**Índice (extraído):** Puesta en marcha, Lo que busco, Mayores y menores, Dominantes, Disminuidos, Aumentados, Puentes, Sustituto tritonal, Ejemplos, Lo que encuentro. (ver PDF para las páginas completas).")
    st.info("Puedes descargar/abrir el PDF completo en el enlace de la barra lateral.")
    st.subheader("Fragmentos útiles (ejemplos rápidos del libro)")
    st.write("- Tipos de modulaciones: modulación por acorde pivote, por dominante secundario, por sustituto tritonal. :contentReference[oaicite:6]{index=6}")
    st.write("- Círculo de quintas: utilidad para modulaciones suaves y la compartición de 6/7 notas entre vecinos. :contentReference[oaicite:7]{index=7}")
    st.write("- Glue mágico: la melodía como pegamento; si la melodía es buena, los acordes conectan. :contentReference[oaicite:8]{index=8}")
    st.markdown("---")
    st.subheader("Visualizador PDF (abrir en nueva pestaña si el iframe no carga)")
    try:
        st.markdown(f"<iframe src='{PDF_PATH}' width='100%' height='600'></iframe>", unsafe_allow_html=True)
    except Exception:
        st.warning("Si el iframe no se muestra, haz click en el enlace del sidebar para abrir el PDF.")

# ------------------ CIRCLE OF FIFTHS ------------------
elif page == "Círculo de Quintas":
    st.header("Círculo de Quintas — visual interactiva")
    st.markdown("El círculo de quintas te permite ver qué tonalidades tienen sostenidos (#) o bemoles (b), y su cercanía para modulaciones suaves.")
    fig, ax = plt.subplots(figsize=(6,6))
    labels = CIRCLE_QUINTS
    n = len(labels)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False)
    xs = np.cos(angles)
    ys = np.sin(angles)
    ax.scatter(xs, ys)
    for i, lab in enumerate(labels):
        ax.text(xs[i]*1.12, ys[i]*1.12, lab, ha='center', va='center', fontsize=12)
    # draw circle
    circle = plt.Circle((0,0), 1.0, fill=False, linestyle='--', alpha=0.3)
    ax.add_artist(circle)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Círculo de Quintas (orden horario)")
    st.pyplot(fig)
    st.markdown("**Usos rápidos:** seleccionar tónica y ver vecinos para modulaciones suaves (comparten 6/7 notas). :contentReference[oaicite:9]{index=9}")
    tonic = st.selectbox("Selecciona tónica para explorar vecinos", options=labels, index=0)
    idx = labels.index(tonic)
    right = labels[(idx+1)%n]
    left = labels[(idx-1)%n]
    st.write(f"Vecino a la derecha (más sostenidos): **{right}** — Vecino a la izquierda (más bemoles): **{left}**")
    st.markdown("Distancia en pasos del círculo:")
    dest = st.selectbox("¿A qué tonalidad te gustaría ir? (modulación)", options=labels, index=2)
    steps = (labels.index(dest) - idx)
    st.write(f"Distancia: {steps} pasos (positivo = horario). Recomendación: 0 = mismo tono; ±1 = muy suave; ±2-3 = moderada; ≥4 = fuerte.")

# ------------------ MODES & CHORDS ------------------
elif page == "Modos y Acordes":
    st.header("Modos griegos y acordes diatónicos")
    tonic_choice = st.selectbox("Elige tónica", ["C","G","D","A","E","B","F#","C#","F","Bb","Eb","Ab","Db","Gb","Cb"])
    mode_choice = st.radio("Modo base", ["major","minor"], index=0)
    scale = build_scale(tonic_choice, 'major' if mode_choice=='major' else 'minor')
    st.subheader("Escala")
    st.write(scale)
    st.subheader("Acordes diatónicos (triada y séptima) y sus cualidades")
    degrees = ["I","ii","iii","IV","V","vi","vii°"]
    rows = []
    for i, deg in enumerate(degrees, start=1):
        tri = triad_from_scale(scale, i)
        sev = seventh_from_scale(scale, i)
        rows.append({"Grado":deg, "Triada": " - ".join(tri), "Séptima": " - ".join(sev)})
    df = pd.DataFrame(rows)
    st.table(df)
    st.markdown("Modos basados en la escala mayor relativa:")
    major_base = scale if mode_choice=='major' else build_scale(index_to_note((note_to_index(tonic_choice)+3)%12), 'major')
    # build modes
    modes = []
    for i in range(7):
        mode_notes = [ major_base[(i+j)%7] for j in range(7) ]
        modes.append(mode_notes)
    mode_names = ["Jónico","Dórico","Frigio","Lidio","Mixolidio","Eólico","Locrio"]
    for name, notes in zip(mode_names, modes):
        st.write(f"**{name}:** {', '.join(notes)}")
    st.info("Esta sección refleja la explicación de modos y su uso (ver capítulo de Modos en el PDF). :contentReference[oaicite:11]{index=11}")

# ------------------ MODULATION INTERACTIVE ------------------
elif page == "Modulación interactiva":
    st.header("Modulación interactiva — sugerencias basadas en el libro")
    origin = st.selectbox("Tonalidad origen", ["C","G","D","A","E","B","F#","C#","F","Bb","Eb","Ab","Db","Gb","Cb"], index=0)
    origin_type = st.radio("Tipo origen", ["major","minor"], index=0)
    target = st.selectbox("Tonalidad destino", ["C","G","D","A","E","B","F#","C#","F","Bb","Eb","Ab","Db","Gb","Cb"], index=3)
    target_type = st.radio("Tipo destino", ["major","minor"], index=0)
    if st.button("Sugerir caminos de modulación"):
        st.write(f"De **{origin} {origin_type}** → **{target} {target_type}**")
        # distance on circle
        try:
            pos_o = CIRCLE_QUINTS.index(origin)
            pos_t = CIRCLE_QUINTS.index(target)
            dist = pos_t - pos_o
        except ValueError:
            dist = None
        if dist is not None:
            st.write("Distancia en círculo (pasos):", dist)
            if abs(dist) <= 1:
                st.success("Modulación muy suave: tonalidades vecinas.")
            elif abs(dist) <= 3:
                st.info("Modulación moderada: usar acordes pivote o dominantes secundarios.")
            else:
                st.warning("Modulación lejana: usar dominantes en cadena o sustitutos tritonales.")
        st.subheader("Sugerencias prácticas (extraídas y adaptadas del PDF):")
        st.write("- Usa un **acorde pivote** que pertenezca a ambas tonalidades (triada común). :contentReference[oaicite:12]{index=12}")
        st.write("- Prueba **dominantes secundarios**: V7 del destino antes de llegar. :contentReference[oaicite:13]{index=13}")
        st.write("- Considera sustituto tritonal (Db7 ↔ G7) para transiciones más coloridas. :contentReference[oaicite:14]{index=14}")
        st.write("- Si quieres suavizar, emplea la escala/nota común como _glue_ en la melodía. :contentReference[oaicite:15]{index=15}")

# ------------------ NOTES / GLUE MAGIC ------------------
elif page == "Notas del autor / Glue mágico":
    st.header("Notas del autor y conceptos clave")
    st.write("Fragmentos y consejos conceptuales extraídos del libro:")
    st.write("- **Glue mágico**: la melodía es el pegamento que une acordes; mantener una nota guía facilita cambios. :contentReference[oaicite:16]{index=16}")
    st.write("- **Tipos de modulaciones**: pivote, dominantes secundarios, sustituto tritonal. No te encierres en etiquetas: lo importante es el acorde destino. :contentReference[oaicite:17]{index=17}")
    st.write("- **Proximidad de acordes**: ordenar acordes por cercanía a una tónica (comparten 3,2,1,0 notas) para construir 'storytelling' tension→resolución. ")
    st.markdown("---")
    st.caption("¿Qué te gustaría agregar después? Opciones: visualizar gráficos del libro como grafos interactivos, generar tablas CSV con todos los acordes en cada tonalidad, crear un 'buscador de puentes' (acorde → tonalidades cercanas), o intentar generar MIDI desde progresiones seleccionadas.")

