# app.py
import streamlit as st
from dataclasses import dataclass
from typing import List

# ---------------------------
# Configuración: círculo de quintas para decidir # vs b
# ---------------------------
# Orden relativo en el círculo: empezando en C y yendo a la derecha (#) y a la izquierda (b)
SHARP_SIDE = ["G","D","A","E","B","F#","C#"]
FLAT_SIDE = ["F","Bb","Eb","Ab","Db","Gb","Cb"]

# Lista de nombres posibles para selector (incluye sostenidos y bemoles comunes)
TONICS = ["C","G","D","A","E","B","F#","C#","F","Bb","Eb","Ab","Db","Gb","Cb",
          "Am","Em","Bm","F#m","C#m","G#m","D#m","Fm","Dm","Gm","Cm","Fm","Bbm"]

# We'll show a shorter, friendly list (common tonics, majors and minors)
TONICS_UI = [
    "C", "G", "D", "A", "E", "B", "F#", "C#",
    "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb",
    "Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m",
    "Dm", "Gm", "Cm", "Fm", "Bbm"
]

# 12-tone mapping
SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

def norm_tonic(s: str) -> str:
    """Normalize user string like 'Am' -> ('A', 'minor') or 'C#' -> ('C#','major')"""
    s = s.strip()
    if s.endswith('m') or s.endswith('min') or s.endswith('minor'):
        # accept 'Am' or 'Amin' etc.
        root = s[0].upper() + (s[1] if len(s)>1 and s[1] in ['#','b'] else '')
        return root, 'minor'
    # if user selected a major tonic (like 'C')
    root = s[0].upper() + (s[1] if len(s)>1 and s[1] in ['#','b'] else '')
    return root, 'major'

def note_to_index(n: str) -> int:
    n = n.replace('♯','#').replace('♭','b')
    if n in SHARP:
        return SHARP.index(n)
    if n in FLAT:
        return FLAT.index(n)
    raise ValueError(f"Nota desconocida: {n}")

def index_to_note(i: int, prefer_flats: bool=False) -> str:
    i = i % 12
    return FLAT[i] if prefer_flats else SHARP[i]

def prefer_flats_for_tonic(tonic: str) -> bool:
    # Decide flats vs sharps using circle of fifths rule:
    if tonic in FLAT_SIDE or tonic.endswith('b'):
        return True
    if tonic in SHARP_SIDE or tonic.endswith('#'):
        return False
    # C default: sharps/no flats
    return False

MAJOR_STEPS = [2,2,1,2,2,2,1]
MINOR_STEPS = [2,1,2,2,1,2,2]  # natural minor

def build_scale(tonic: str, mode: str='major') -> List[str]:
    tonic = tonic.replace('♯','#').replace('♭','b')
    prefer_flats = prefer_flats_for_tonic(tonic)
    start = note_to_index(tonic)
    steps = MAJOR_STEPS if mode=='major' else MINOR_STEPS
    notes = [index_to_note(start, prefer_flats)]
    idx = start
    for s in steps[:-1]:
        idx = (idx + s) % 12
        notes.append(index_to_note(idx, prefer_flats))
    return notes

# chord building by stacking scale degrees (1-3-5) using the scale list (correct spelling)
def triad_from_scale(scale: List[str], degree:int) -> List[str]:
    n = len(scale)
    root = scale[(degree-1) % n]
    third = scale[(degree+1) % n]
    fifth = scale[(degree+3) % n]
    return [root, third, fifth]

def seventh_from_scale(scale: List[str], degree:int) -> List[str]:
    # 1-3-5-7 stacking
    n = len(scale)
    root = scale[(degree-1) % n]
    third = scale[(degree+1) % n]
    fifth = scale[(degree+3) % n]
    seventh = scale[(degree+5) % n]
    return [root, third, fifth, seventh]

def triad_quality_by_intervals(triad: List[str]) -> str:
    # Determine quality by intervals in semitones
    a = note_to_index(triad[0])
    b = note_to_index(triad[1])
    c = note_to_index(triad[2])
    i1 = (b - a) % 12
    i2 = (c - b) % 12
    if i1==4 and i2==3:
        return "maj"
    if i1==3 and i2==4:
        return "min"
    if i1==3 and i2==3:
        return "dim"
    return "unknown"

def seventh_quality_by_intervals(sev: List[str], triad_quality: str) -> str:
    # Check interval between root and 7th
    a = note_to_index(sev[0])
    d = note_to_index(sev[3])
    interval = (d - a) % 12
    # typical naming:
    if triad_quality=="maj" and interval==11:
        return "maj7"
    if triad_quality=="maj" and interval==10:
        return "7"     # dominant 7
    if triad_quality=="min" and interval==10:
        return "m7"
    if triad_quality=="dim" and interval==10:
        return "m7b5"
    # fallback
    return "7"

# Modes: rotate major scale
MODE_NAMES = ["Jónico (Ionian)","Dórico (Dorian)","Frigio (Phrygian)",
              "Lidio (Lydian)","Mixolidio (Mixolydian)","Eólico (Aeolian)","Locrio (Locrian)"]

def build_modes_from_major(major_scale: List[str]) -> List[List[str]]:
    modes = []
    n = len(major_scale)
    for i in range(n):
        mode = [major_scale[(i + j) % n] for j in range(n)]
        modes.append(mode)
    return modes

# ---------------------------
# UI
# ---------------------------
st.set_page_config(page_title="Modulador — Escalas y Modos", layout="wide")
st.title("🔷 Modulador — Escalas, Acordes y Modos (Mayor & Menor)")

st.markdown("Selecciona la tonalidad (elige mayor o menor). El sistema usa el **círculo de quintas** para decidir si mostrar sostenidos (`#`) o bemoles (`b`).")

# Choose tonic and mode
col1, col2 = st.columns([1,1])
with col1:
    tonic_input = st.selectbox("Tonalidad (base)", options=[
        "C","G","D","A","E","B","F#","C#",
        "F","Bb","Eb","Ab","Db","Gb","Cb",
        "Am","Em","Bm","F#m","C#m","G#m","D#m",
        "Dm","Gm","Cm","Fm","Bbm"
    ], index=0)
with col2:
    # Normalize selection into root / mode
    # If selection ends with 'm' treat as minor; otherwise ask radio
    if tonic_input.endswith('m') or tonic_input.endswith('m'):
        # treat as minor
        root_note, forced_mode = tonic_input[:-1].upper(), "minor"
        _mode = st.radio("Modo", options=["minor"], index=0, disabled=True)
    else:
        root_note = tonic_input
        _mode = st.radio("Modo", options=["major","minor"], index=0)

# allow user to override accidental display preference
auto_prefer_flats = prefer_flats_for_tonic(root_note)
prefer_choice = st.radio("Notación preferida (automático/cambiar):",
                        options=["Automático (círculo de quintas)", "Forzar #: sostenidos", "Forzar b: bemoles"],
                        index=0)
if prefer_choice == "Forzar #: sostenidos":
    prefer_flats = False
elif prefer_choice == "Forzar b: bemoles":
    prefer_flats = True
else:
    prefer_flats = auto_prefer_flats

# compute actual tonic to use for spelling (if user selected minor mode but root_note from selection might be major)
# Use root_note and mode _mode to build scale
try:
    # if user selected minor via radio, keep root_note as is; but if they selected a minor tonic like "Am" initial, root_note already set
    tonic = root_note
    mode = _mode
    # build scale
    scale = build_scale(tonic, 'major' if mode=='major' else 'minor')
except Exception as e:
    st.error(f"Error construyendo la escala: {e}")
    st.stop()

# Relative keys
if mode == 'major':
    # relative minor is vi degree
    rel_minor = scale[5]
    rel_text = f"La relativa menor de {tonic} mayor es: **{rel_minor}m**"
else:
    # relative major is +3 semitones (minor tonic -> major tonic)
    rel_major_idx = (note_to_index(tonic) + 3) % 12
    rel_major = index_to_note(rel_major_idx, prefer_flats)
    rel_text = f"La relativa mayor de {tonic} menor es: **{rel_major}**"

# Display basic info
st.markdown("---")
st.subheader("🔹 Información básica")
st.write(f"**Tonalidad seleccionada:** {tonic}  ({'Mayor' if mode=='major' else 'Menor'})")
st.write(rel_text)
st.write(f"**Notación usada:** {'bemoles (b)' if prefer_flats else 'sostenidos (#)'} (según círculo de quintas / elección)")

# display scale
st.subheader("🔸 Escala")
st.write("Notas de la escala:", ", ".join(scale))

# Diatonic chords
st.subheader("🔸 Acordes diatónicos (triada y 7ª) con su calidad")
cols = st.columns([1,1,1,1])
headers = ["Grado","Triada (notas)","Calidad","Séptima (notas / tipo)"]
for c,h in zip(cols, headers):
    c.write(f"**{h}**")

degrees = ["I","ii","iii","IV","V","vi","vii°"]
triads = []
sevenths = []
for i, deg in enumerate(degrees, start=1):
    tri = triad_from_scale(scale, i)
    tri_q = triad_quality_by_intervals(tri)
    sev = seventh_from_scale(scale, i)
    sev_q = seventh_quality_by_intervals(sev, tri_q)
    triads.append((deg, tri, tri_q, sev, sev_q))

# print rows
for deg, tri, tri_q, sev, sev_q in triads:
    c1, c2, c3, c4 = st.columns([1,2,1,2])
    c1.write(f"**{deg}**")
    c2.write(f"{tri[0]} – {tri[1]} – {tri[2]}")
    # human friendly quality names
    qtext = {"maj":"Mayor","min":"Menor","dim":"Disminuido","unknown":"Desconocido"}.get(tri_q, tri_q)
    c3.write(qtext)
    c4.write(f"{sev[0]} – {sev[1]} – {sev[2]} – {sev[3]}  ({sev_q})")

# Modes
st.subheader("🔸 Modos griegos (basados en la escala mayor relativa)")
# Build modes from the major scale that corresponds to this tonal center.
if mode == 'major':
    major_base = scale
else:
    # If user chose minor, show modes from the relative major
    # relative major index:
    rel_maj_idx = (note_to_index(tonic) + 3) % 12
    rel_maj = index_to_note(rel_maj_idx, prefer_flats)
    major_base = build_scale(rel_maj, 'major')

modes = build_modes_from_major(major_base)
for name, m in zip(MODE_NAMES, modes):
    st.write(f"**{name}:** " + ", ".join(m))

st.markdown("---")
st.info("Este módulo muestra la teoría básica: escala, acordes diatónicos (triada y séptima) y modos. Próximos pasos que puedo añadir: inversiones, voicings (drop2), acordes 9/11/13, modulaciones automáticas, piano-roll y exportar MIDI/sonido. Dime cuál quieres que agregue primero.")
