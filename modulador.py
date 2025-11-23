# modulador_enhanced.py
import streamlit as st
import numpy as np
from typing import List, Tuple
import mido
from io import BytesIO

# -----------------------------
# Config & constants
# -----------------------------
PDF_LOCAL_PATH = "Brian Callipari - Armonía Ilustrada - Español.pdf"  # Cambia a path relativo si está en el repo

# Circle order (clockwise) — Majors outer
CIRCLE_QUINTS_MAJOR = [
    "C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "Eb", "Bb", "F"  # Ajustado para consistencia
]
# Relative minors inner
CIRCLE_QUINTS_MINOR = [
    "Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "A#m", "Em", "Cm", "Gm", "Dm"  # Relativos
]

# Names for UI lists
TONICS_UI = [
    "C","G","D","A","E","B","F#","C#","F","Bb","Eb","Ab","Db","Gb","Cb",
    "Am","Em","Bm","F#m","C#m","G#m","D#m","Dm","Gm","Cm","Fm","Bbm"
]
SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
MAJOR_STEPS = [2,2,1,2,2,2,1]
MINOR_STEPS = [2,1,2,2,1,2,2]

# color map for node types
COLOR_TONIC = "#FFB6C1"  # rosa (tonic)
COLOR_MINOR = "#87CEFA"  # azul (minor)
COLOR_DOM = "#FFD700"   # amarillo (dominant)
COLOR_DIM = "#9370DB"   # morado (dim)
COLOR_NEUTRAL = "#DDDDDD"

# -----------------------------
# Helper functions (notes, scales)
# -----------------------------
def normalize_note(s: str) -> str:
    s = s.strip().replace("♯","#").replace("♭","b")
    return s

def note_to_index(n: str) -> int:
    n = normalize_note(n)
    if n in SHARP:
        return SHARP.index(n)
    if n in FLAT:
        return FLAT.index(n)
    # Handle minors (e.g., "Am" -> "A")
    if n.endswith("m"):
        return note_to_index(n[:-1])
    raise ValueError(f"Unknown note: {n}")

def index_to_note(i: int, prefer_flats=False) -> str:
    i = i % 12
    return FLAT[i] if prefer_flats else SHARP[i]

def prefer_flats_for_tonic(tonic: str) -> bool:
    left = ['F','Bb','Eb','Ab','Db','Gb','Cb']
    tonic = normalize_note(tonic)
    if tonic.endswith('m'):
        tonic = tonic[:-1]  # Para menores, basarse en la raíz
    if tonic in left or tonic.endswith('b'):
        return True
    return False

def build_scale(tonic: str, mode: str='major') -> List[str]:
    tonic_root = tonic[:-1] if tonic.endswith('m') else tonic
    is_minor = tonic.endswith('m')
    tonic = normalize_note(tonic_root)
    prefer_flats = prefer_flats_for_tonic(tonic)
    start = note_to_index(tonic)
    steps = MINOR_STEPS if is_minor or mode=='minor' else MAJOR_STEPS
    notes = [index_to_note(start, prefer_flats)]
    idx = start
    for s in steps[:-1]:
        idx = (idx + s) % 12
        notes.append(index_to_note(idx, prefer_flats))
    return notes

def triad_from_scale(scale: List[str], degree: int) -> List[str]:
    n = len(scale)
    return [scale[(degree-1)%n], scale[(degree+1)%n], scale[(degree+3)%n]]

def seventh_from_scale(scale: List[str], degree: int) -> List[str]:
    n = len(scale)
    return [scale[(degree-1)%n], scale[(degree+1)%n], scale[(degree+3)%n], scale[(degree+5)%n]]

def intervals_of_mode(mode: str) -> str:
    patterns = {
        "Ionian":"T T S T T T S",
        "Dorian":"T S T T T S T",
        "Phrygian":"S T T T S T T",
        "Lydian":"T T T S T T S",
        "Mixolydian":"T T S T T S T",
        "Aeolian":"T S T T S T T",
        "Locrian":"S T T S T T T"
    }
    return patterns.get(mode, "")

# -----------------------------
# Chord builder & identifier (expanded)
# -----------------------------
BASIC_CHORD_TEMPLATES = {
    "maj": (0,4,7),
    "min": (0,3,7),
    "dim": (0,3,6),
    "aug": (0,4,8),
    "sus2": (0,2,7),
    "sus4": (0,5,7),
    "add9": (0,4,7,14),
    "7": (0,4,7,10),
    "maj7": (0,4,7,11),
    "m7": (0,3,7,10),
    "m9": (0,3,7,10,14),
    "m7b5": (0,3,6,10),
    "dim7": (0,3,6,9),
    "9": (0,4,7,10,14),
    "11": (0,4,7,10,14,17),
    "13": (0,4,7,10,14,17,21)
}

def build_chord(root: str, chord_type: str, prefer_flats=False) -> List[str]:
    root_idx = note_to_index(root)
    if chord_type not in BASIC_CHORD_TEMPLATES:
        raise ValueError("Chord type not supported")
    formula = BASIC_CHORD_TEMPLATES[chord_type]
    notes = [index_to_note(root_idx + i, prefer_flats) for i in formula]
    return notes

def chord_name_from_notes(notes: List[str]) -> Tuple[str, List[str]]:
    pcs = sorted(set(note_to_index(n) % 12 for n in notes))
    for root_pc in pcs:
        for name, formula in BASIC_CHORD_TEMPLATES.items():
            candidate = sorted((root_pc + i) % 12 for i in formula)
            if candidate == pcs:
                root_name = index_to_note(root_pc)
                chord_notes = [index_to_note(root_pc + i) for i in formula]
                return f"{root_name}{name if name != 'maj' else ''}", chord_notes
    return ("Unknown", notes)  # Mejorado para coincidencias exactas

# -----------------------------
# Modulation helpers
# -----------------------------
def find_pivot_chords(origin: str, target: str, min_common=2) -> List[Tuple[List[str], List[str]]]:
    s_o = build_scale(origin, 'major')
    s_t = build_scale(target, 'major')
    o_chords = [triad_from_scale(s_o, i) for i in range(1,8)] + [seventh_from_scale(s_o, i) for i in range(1,8)]
    t_chords = [triad_from_scale(s_t, i) for i in range(1,8)] + [seventh_from_scale(s_t, i) for i in range(1,8)]
    pairs = []
    for oc in o_chords:
        for tc in t_chords:
            oc_set = set(note_to_index(n) for n in oc)
            tc_set = set(note_to_index(n) for n in tc)
            common = oc_set.intersection(tc_set)
            if len(common) >= min_common:
                pairs.append((oc, tc))
    seen = set()
    out = []
    for oc, tc in pairs:
        key = (tuple(sorted(oc)), tuple(sorted(tc)))
        if key not in seen:
            seen.add(key)
            out.append((oc, tc))
    return out[:10]  # Aumentado a 10 para más opciones

# -----------------------------
# MIDI helpers
# -----------------------------
def note_to_midi(note: str, octave: int = 4) -> int:
    base = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
            'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    n = normalize_note(note)
    return 12 * (octave + 1) + base.get(n, 0)  # C4 = 60

def create_midi_from_notes(notes: List[str], tempo: int = 120, duration: int = 480) -> BytesIO:
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))
    for note in notes + notes[::-1]:  # Ascending + descending
        midi_note = note_to_midi(note)
        track.append(mido.Message('note_on', note=midi_note, velocity=64, time=0))
        track.append(mido.Message('note_off', note=midi_note, velocity=0, time=duration))
    buffer = BytesIO()
    mid.save(file=buffer)
    buffer.seek(0)
    return buffer

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Modulador Musical — Avanzado", layout="wide")
st.title("🎹 Modulador Musical: Ayuda para Músicos")

# Sidebar
st.sidebar.title("Menú")
label_concepts = st.sidebar.text_input("Etiqueta para conceptos/ayuda", value="Conceptos Básicos")
page = st.sidebar.radio("Sección", [
    "Inicio", "Círculo de Quintas (Gráfico)", "Modos & Acordes (Vista Dual)",
    "Modulación Avanzada", "Constructor/Identificador de Acordes", label_concepts
])
st.sidebar.markdown("---")
st.sidebar.markdown(f"[Descargar PDF del libro]({PDF_LOCAL_PATH})")

# --------------
# Page: Inicio (nueva)
# --------------
if page == "Inicio":
    st.header("Bienvenido al Modulador Musical")
    st.markdown("""
    Esta app te ayuda con:
    - **Círculo de Quintas**: Visualiza y explora tonalidades.
    - **Modos y Acordes**: Construye escalas, modos y acordes.
    - **Modulaciones**: Encuentra transiciones suaves entre tonalidades.
    - **Constructor de Acordes**: Crea y identifica acordes, incluyendo exportación MIDI.
    - **Conceptos**: Guía básica basada en 'Armonía Ilustrada' de Brian Callipari.
    
    ¡Explora las secciones del menú lateral! Si quieres agregar más features (como piano-roll o gráficos interactivos), dime.
    """)

# --------------
# Page: Circle (SVG mejorado con inner minors)
# --------------
elif page == "Círculo de Quintas (Gráfico)":
    st.header("Círculo de Quintas — Vista Gráfica Mejorada")
    st.markdown("Colores: Rosa = Tónicas mayores, Azul = Relativas menores, Amarillo = Dominantes, Morado = Disminuidos.")
    
    # SVG con dos anillos
    majors = CIRCLE_QUINTS_MAJOR
    minors = CIRCLE_QUINTS_MINOR
    n = 12  # 12 posiciones
    outer_radius = 160
    inner_radius = 120
    center_x = 200
    center_y = 200
    node_radius = 20
    
    def node_color(label, is_minor=False):
        if "m" in label:
            return COLOR_MINOR
        if label == "C":
            return COLOR_TONIC
        if label in ["G","D","A","E","B","F#","C#"]:
            return COLOR_DOM
        if label in ["B","F#","C#","Dim"]:
            return COLOR_DIM
        return COLOR_NEUTRAL
    
    svg = f'<svg width="100%" height="420" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">'
    svg += f'<defs><style>.lbl{{font-family:Arial; font-size:14px; text-anchor:middle}}</style></defs>'
    
    # Outer (majors)
    for i, lab in enumerate(majors):
        angle = 2 * np.pi * i / n - np.pi / 2
        x = center_x + outer_radius * np.cos(angle)
        y = center_y + outer_radius * np.sin(angle)
        color = node_color(lab)
        svg += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{node_radius}" fill="{color}" stroke="#333" />'
        svg += f'<text x="{x:.2f}" y="{y+5:.2f}" class="lbl">{lab}</text>'
    
    # Inner (minors)
    for i, lab in enumerate(minors):
        angle = 2 * np.pi * i / n - np.pi / 2
        x = center_x + inner_radius * np.cos(angle)
        y = center_y + inner_radius * np.sin(angle)
        color = node_color(lab, is_minor=True)
        svg += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{node_radius}" fill="{color}" stroke="#333" />'
        svg += f'<text x="{x:.2f}" y="{y+5:.2f}" class="lbl">{lab}</text>'
    
    svg += "</svg>"
    st.markdown(svg, unsafe_allow_html=True)
    
    st.markdown("**Interactúa:** Selecciona una tónica y ve vecinos.")
    tonic = st.selectbox("Selecciona tónica:", options=TONICS_UI, index=0)
    # Lógica similar, pero ahora maneja menores
    is_minor = tonic.endswith("m")
    tonic_root = tonic[:-1] if is_minor else tonic
    idx = CIRCLE_QUINTS_MAJOR.index(tonic_root) if not is_minor else CIRCLE_QUINTS_MINOR.index(tonic)
    right = CIRCLE_QUINTS_MAJOR[(idx+1)%n] if not is_minor else CIRCLE_QUINTS_MINOR[(idx+1)%n]
    left = CIRCLE_QUINTS_MAJOR[(idx-1)%n] if not is_minor else CIRCLE_QUINTS_MINOR[(idx-1)%n]
    st.write(f"Vecino derecho (más sostenidos): **{right}{'m' if is_minor else ''}**")
    st.write(f"Vecino izquierdo (más bemoles): **{left}{'m' if is_minor else ''}**")
    dest = st.selectbox("¿A qué tonalidad quieres ir?", options=TONICS_UI, index=2)
    # Distancia simplificada
    dest_root = dest[:-1] if dest.endswith("m") else dest
    dist = CIRCLE_QUINTS_MAJOR.index(dest_root) - idx if not is_minor else CIRCLE_QUINTS_MINOR.index(dest) - idx
    st.write(f"Distancia en pasos: {dist} (positivo = horario). Recomendación: ±1 suave; ±2-3 moderada; ≥4 fuerte.")

# Otras páginas permanecen similares, pero agrego MIDI donde tiene sentido
# Por ejemplo, en "Modos & Acordes"
elif page == "Modos & Acordes (Vista Dual)":
    # ... (código original)
    # Al final de cada modo, agrega:
    if st.button(f"Exportar {name} como MIDI"):
        midi_buffer = create_midi_from_notes(mode_notes)
        st.download_button(label="Descargar MIDI", data=midi_buffer, file_name=f"{tonic}_{name}.mid", mime="audio/midi")

# En "Modulación Avanzada", después de pivots:
    if pivots:
        example_prog = [s_o[0], pivots[0][0][0], pivots[0][1][0], s_t[0]]  # Simple I - pivot - pivot - I
        if st.button("Exportar progresión de ejemplo como MIDI"):
            midi_buffer = create_midi_from_notes(example_prog)
            st.download_button(label="Descargar MIDI", data=midi_buffer, file_name="modulacion.mid", mime="audio/midi")

# En "Constructor/Identificador de Acordes", después de generar:
    if st.button("Exportar acorde como MIDI"):
        midi_buffer = create_midi_from_notes(notes)
        st.download_button(label="Descargar MIDI", data=midi_buffer, file_name=f"{root}{chord_type}.mid", mime="audio/midi")

# ... (el resto del código sigue igual, con ajustes menores para consistencia)

# Footer
st.markdown("---")
st.markdown(f"PDF (descarga): [{PDF_LOCAL_PATH}]({PDF_LOCAL_PATH})")
st.caption("App mejorada basada en 'Armonía Ilustrada'. Ahora con MIDI export y círculo completo. Si necesitas más cambios, ¡dime!")
