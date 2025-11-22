# app_enhanced.py
import streamlit as st
import numpy as np
from typing import List, Tuple

# -----------------------------
# Config & constants
# -----------------------------
PDF_LOCAL_PATH = "/mnt/data/Brian Callipari - Armonía Ilustrada - Español.pdf"

# Circle order (clockwise) — 14 positions
CIRCLE_QUINTS = [
    "C","G","D","A","E","B","F#","C#","Gb","Db","Ab","Eb","Bb","F"
]

# Names for UI lists
TONICS_UI = [
    "C","G","D","A","E","B","F#","C#","F","Bb","Eb","Ab","Db","Gb","Cb",
    "Am","Em","Bm","F#m","C#m","G#m","D#m","Dm","Gm","Cm","Fm","Bbm"
]

SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

MAJOR_STEPS = [2,2,1,2,2,2,1]
MINOR_STEPS = [2,1,2,2,1,2,2]

# color map for node types (you can tweak the hex colors)
COLOR_TONIC = "#FFB6C1"     # rosa (tonic)
COLOR_MINOR = "#87CEFA"     # azul
COLOR_DOM = "#FFD700"       # amarillo
COLOR_DIM = "#9370DB"       # morado
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
    raise ValueError(f"Unknown note: {n}")

def index_to_note(i: int, prefer_flats=False) -> str:
    i = i % 12
    return FLAT[i] if prefer_flats else SHARP[i]

def prefer_flats_for_tonic(tonic: str) -> bool:
    left = ['F','Bb','Eb','Ab','Db','Gb','Cb']
    tonic = normalize_note(tonic)
    if tonic in left or tonic.endswith('b'):
        return True
    return False

def build_scale(tonic: str, mode: str='major') -> List[str]:
    tonic = normalize_note(tonic)
    prefer_flats = prefer_flats_for_tonic(tonic)
    start = note_to_index(tonic)
    steps = MAJOR_STEPS if mode=='major' else MINOR_STEPS
    notes = [index_to_note(start, prefer_flats)]
    idx = start
    for s in steps[:-1]:
        idx = (idx + s) % 12
        notes.append(index_to_note(idx, prefer_flats))
    return notes

def triad_from_scale(scale: List[str], degree: int) -> List[str]:
    n = len(scale)
    return [ scale[(degree-1)%n], scale[(degree+1)%n], scale[(degree+3)%n] ]

def seventh_from_scale(scale: List[str], degree: int) -> List[str]:
    n = len(scale)
    return [ scale[(degree-1)%n], scale[(degree+1)%n], scale[(degree+3)%n], scale[(degree+5)%n] ]

def intervals_of_mode(mode: str) -> str:
    """Return T/S pattern for mode name (common patterns)."""
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
# Chord builder & identifier (basic)
# -----------------------------
BASIC_CHORD_TEMPLATES = {
    "maj": (0,4,7),
    "min": (0,3,7),
    "dim": (0,3,6),
    "aug": (0,4,8),
    "sus2": (0,2,7),
    "sus4": (0,5,7),
    "7": (0,4,7,10),
    "maj7": (0,4,7,11),
    "m7": (0,3,7,10),
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
    notes = [ index_to_note(root_idx + i, prefer_flats) for i in formula ]
    return notes

def chord_name_from_notes(notes: List[str]) -> Tuple[str, List[str]]:
    """Try to identify chord name from pitch classes (simple heuristic).
       Returns (name, normalized chord notes)."""
    # normalize note names to pitch classes
    pcs = sorted({note_to_index(n)%12 for n in notes})
    # brute force common roots and templates
    for root_pc in pcs:
        for name, formula in BASIC_CHORD_TEMPLATES.items():
            candidate = sorted(((root_pc + i) % 12) for i in formula)
            if set(candidate).issubset(set(pcs)) and len(candidate) <= len(pcs):
                root_name = index_to_note(root_pc)
                chord_notes = [ index_to_note(root_pc + i) for i in formula ]
                return f"{root_name}{name if name!='maj' else ''}", chord_notes
    return ("Unknown", notes)

# -----------------------------
# Modulation helpers
# -----------------------------
def find_pivot_chords(origin: str, target: str, min_common=2) -> List[Tuple[List[str],List[str]]]:
    """Return pairs (origin_chord, target_chord) that share >= min_common pitch classes."""
    s_o = build_scale(origin, 'major')
    s_t = build_scale(target, 'major')
    o_chords = [ triad_from_scale(s_o, i) for i in range(1,8) ] + [ seventh_from_scale(s_o, i) for i in range(1,8) ]
    t_chords = [ triad_from_scale(s_t, i) for i in range(1,8) ] + [ seventh_from_scale(s_t, i) for i in range(1,8) ]
    pairs = []
    for oc in o_chords:
        for tc in t_chords:
            oc_set = {note_to_index(n) for n in oc}
            tc_set = {note_to_index(n) for n in tc}
            common = oc_set.intersection(tc_set)
            if len(common) >= min_common:
                pairs.append((oc, tc))
    # unique and limit
    seen = set()
    out = []
    for oc, tc in pairs:
        key = (tuple(oc), tuple(tc))
        if key in seen: continue
        seen.add(key)
        out.append((oc, tc))
    return out[:8]

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Modulador — avanzado", layout="wide")
st.title("🎚️ Modulador interactivo — Escalas, Modos, Acordes, Modulaciones")

# Sidebar (editable labels)
st.sidebar.title("Menú")
label_concepts = st.sidebar.text_input("Etiqueta para conceptos/ayuda", value="Conceptos básicos")
page = st.sidebar.radio("Sección", [
    "Círculo de Quintas (gráfico)", "Modos & Acordes (dual view)",
    "Modulación avanzada", "Constructor/Identificador de acordes", label_concepts
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"[Descargar PDF del libro]({PDF_LOCAL_PATH})")

# --------------
# Page: Circle (SVG)
# --------------
if page == "Círculo de Quintas (gráfico)":
    st.header("Círculo de Quintas — vista gráfica")
    st.markdown("Los colores: rosa = tónicas, azul = relativos / menores, amarillo = dominantes, morado = disminuidos.")
    # SVG circle generation
    labels = CIRCLE_QUINTS
    n = len(labels)
    radius = 140
    center_x = 160
    center_y = 160
    node_radius = 18

    def node_color(label):
        # assign colors roughly:
        if label == "C":
            return COLOR_TONIC
        # minor relatives (we highlight minor roots in blue)
        if label in ["Am","Em","Bm","F#m","C#m","G#m","D#m"]:
            return COLOR_MINOR
        # dominants (fifth relationships) highlight in yellow if they are V of something (approx)
        if label in ["G","D","A","E","B","F#","C#"]:
            return COLOR_DOM
        # diminished placeholders
        if label in ["B","F#","C#"]:
            return COLOR_DIM
        return COLOR_NEUTRAL

    # Build SVG
    svg = f'<svg width="100%" height="340" viewBox="0 0 320 320" xmlns="http://www.w3.org/2000/svg">'
    svg += f'<defs><style>.lbl{{font-family:Arial; font-size:12px; text-anchor:middle}}</style></defs>'
    for i, lab in enumerate(labels):
        angle = 2 * np.pi * i / n - np.pi/2
        x = center_x + radius * np.cos(angle)
        y = center_y + radius * np.sin(angle)
        color = node_color(lab)
        svg += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{node_radius}" fill="{color}" stroke="#333" />'
        svg += f'<text x="{x:.2f}" y="{y+5:.2f}" class="lbl">{lab}</text>'
    svg += "</svg>"

    st.markdown(svg, unsafe_allow_html=True)
    st.markdown("**Interactúa:** selecciona una tónica y te muestro vecinos y recomendaciones.")
    tonic = st.selectbox("Selecciona tónica:", options=CIRCLE_QUINTS, index=0)
    idx = CIRCLE_QUINTS.index(tonic)
    right = CIRCLE_QUINTS[(idx+1)%n]
    left = CIRCLE_QUINTS[(idx-1)%n]
    st.write(f"Vecino derecho (más sostenidos): **{right}**")
    st.write(f"Vecino izquierdo (más bemoles): **{left}**")
    dest = st.selectbox("¿A qué tonalidad quieres ir?", options=CIRCLE_QUINTS, index=2)
    steps = CIRCLE_QUINTS.index(dest) - idx
    st.write(f"Distancia en pasos: {steps} (positivo = horario). Recomendación: 0 mismo; ±1 muy suave; ±2-3 moderada; ≥4 fuerte.")

# --------------
# Page: Modes & chords (dual view)
# --------------
elif page == "Modos & Acordes (dual view)":
    st.header("Modos y Acordes — vista doble (grado y desde tónica)")

    tonic = st.selectbox("Elige la tónica base", options=SHARP+FLAT, index=0)
    mode_choice = st.radio("Visión", options=["Modalidad: modos clásicos (ej: Jónico en C)", "Modo relativo iniciado en la tónica (ej: C Frigio)"])

    # Build major base (for modes)
    major_scale = build_scale(tonic, 'major')
    st.subheader("Modo clásico — inicio por grado (ej: Jónico, Dórico, ...)")
    mode_names = ["Jónico (Ionian)","Dórico (Dorian)","Frigio (Phrygian)","Lidio (Lydian)",
                  "Mixolidio (Mixolydian)","Eólico (Aeolian)","Locrio (Locrian)"]
    for i, name in enumerate(mode_names):
        mode_notes = [ major_scale[(i+j)%7] for j in range(7) ]
        pattern = intervals_of_mode(name.split()[0])
        st.write(f"**{name}** → {', '.join(mode_notes)}  —  Forma: {pattern}")

    st.markdown("---")
    st.subheader("Modo empezando en la tónica seleccionada")
    # For each mode, show its form if started from tonic
    # We will compute the mode intervals relative to the tonic
    for i, name in enumerate(mode_names):
        # to start mode i on tonic, rotate the major_scale so that mode i has tonic as its first
        # Actually derive by taking mode that has the tonic as one of its scale degrees and rotate accordingly
        # Simpler: compute mode scale by starting from tonic and using pattern of that mode.
        mode_name_short = name.split()[0]
        # derive pattern for mode -> we'll emulate by rotating major to have tonic appear
        # find which mode (i0) in major_scale contains tonic at position j such that major_scale[j]==tonic
        # Simpler approach: build the mode by computing intervals for that mode starting on tonic
        mode_steps = {
            "Jónico":[2,2,1,2,2,2,1],
            "Dórico":[2,1,2,2,2,1,2],
            "Frigio":[1,2,2,2,1,2,2],
            "Lidio":[2,2,2,1,2,2,1],
            "Mixolidio":[2,2,1,2,2,1,2],
            "Eólico":[2,1,2,2,1,2,2],
            "Locrio":[1,2,2,1,2,2,2]
        }
        steps = mode_steps[mode_name_short]
        # build mode starting from tonic
        notes = []
        idx = note_to_index(tonic)
        prefer_flats = prefer_flats_for_tonic(tonic)
        notes.append(index_to_note(idx, prefer_flats))
        for s in steps[:-1]:
            idx = (idx + s) % 12
            notes.append(index_to_note(idx, prefer_flats))
        st.write(f"**{name} iniciando en {tonic}:** {', '.join(notes)}  —  Forma: {intervals_of_mode(mode_name_short)}")

# --------------
# Page: Modulation advanced
# --------------
elif page == "Modulación avanzada":
    st.header("Modulación — introducción profesional")
    st.markdown("""
**Modulación**: cambio de tonalidad dentro de una obra.  
Un proceso musical que idealmente pasa desapercibido para el oyente y que se puede dividir en tres momentos:
1. **Tonalidad de partida** — zona estable.
2. **Zona neutra / transición** — aquí aparece el *acorde pivote* o el recurso (dominante, cromatismo, sustituto).
3. **Tonalidad de llegada** — zona estable en la nueva tonalidad.

**Nota**: Una modulacion no es lo mismo que una cadencia.  
- *Cadencia* reafirma el final de una sección.  
- *Modulación* es un proceso que nos lleva a otra tonalidad sin sentir una pausa significativa.
""")

    st.subheader("Tipos principales (resumen)")
    st.write("- **Diatónica (por acorde pivote)**: se usa un acorde que pertenece a ambas tonalidades (ej.: Dm en C y Dm en F) — ideal para modulaciones suaves.")
    st.write("- **Cromática**: usa movimientos cromáticos (acorde disminuido de paso, cromatismos en la voz líder) para cambiar el centro tonal.")
    st.write("- **Enarmónica**: usar notas/enarmonías equivalentes (ej.: C# = Db) para reinterpretar un acorde y cambiar la tonalidad — muy útil para cambios lejanos o modulaciones dramáticas.")

    st.markdown("---")
    st.subheader("Herramienta: genera rutas y acordes sugeridos")
    origin = st.selectbox("Tonalidad origen", CIRCLE_QUINTS, index=0)
    target = st.selectbox("Tonalidad destino", CIRCLE_QUINTS, index=3)
    if st.button("Generar rutas de modulación"):
        st.write(f"**De** {origin} **a** {target}")
        # distance
        io = CIRCLE_QUINTS.index(origin)
        it = CIRCLE_QUINTS.index(target)
        dist = it - io
        st.write(f"Distancia en el círculo: {dist} pasos")
        if abs(dist) <= 1:
            st.success("Cambio cercano — prueba pivote o 'shared chord'.")
        elif abs(dist) <= 3:
            st.info("Cambio medio — dominante secundaria o cadena corta de dominantes.")
        else:
            st.warning("Cambio lejano — considera sustitutos tritonales o cadenas de dominantes.")

        # Show diatonic chords of both keys (triads + sevenths)
        s_o = build_scale(origin, 'major')
        s_t = build_scale(target, 'major')
        st.write("**Acordes diatónicos (origen)**")
        for i in range(1,8):
            tri = triad_from_scale(s_o, i)
            sev = seventh_from_scale(s_o, i)
            st.write(f"{i}. {tri}  → 7ª: {sev}")
        st.write("**Acordes diatónicos (destino)**")
        for i in range(1,8):
            tri = triad_from_scale(s_t, i)
            sev = seventh_from_scale(s_t, i)
            st.write(f"{i}. {tri}  → 7ª: {sev}")

        # Pivot chords
        st.subheader("Acordes pivote sugeridos")
        pivots = find_pivot_chords(origin, target, min_common=2)
        if pivots:
            for oc, tc in pivots:
                st.write(f"Origen: {oc}  ↔  Destino: {tc}")
        else:
            st.write("No se identificaron pivotes con 2+ notas en común — considera dominantes o cromatismos.")

        # Suggested routes examples (preformatted)
        st.subheader("Rutas sugeridas (ejemplos concretos)")
        st.write("1) **Diatónica (pivote)** — I (origen) → acorde pivote → I (destino)")
        st.write("   Ejemplo con séptimas / colores: Cmaj7 → Dm7 (pivot) → Fmaj7")
        st.write("2) **Dominante secundaria** — prepara con ii → V → I (destino)")
        st.write("   Ejemplo: Cmaj7 → Dm7 → G7 → C (o G7 → C → Fmaj7 si vas a F)")
        st.write("3) **Cromática** — passing diminished / cromatismo en la voz")
        st.write("   Ejemplo: Cmaj7 → C#dim7 → Dm7 → Fmaj7 (usa notas comunes como glue)")
        st.write("4) **Enarmónica / sustituto tritonal**")
        st.write("   Ejemplo: C → Db7 (como sustituto de G7) → F")

        st.markdown("**Acordes de paso útiles**: sus2, sus4, add9, m7, maj7, dim7, tritone substitute (bII7).")
        st.info("Consejo pedagógico: para estudiantes novatos, muestra progresiones con pocas notas en el bajo (inversiones) y acordes de 4 notas (7s) para mantener textura rica pero suave.")

# --------------
# Page: Chord builder / identifier
# --------------
elif page == "Constructor/Identificador de acordes":
    st.header("Constructor y analizador de acordes")

    st.subheader("Construir un acorde")
    root = st.selectbox("Seleccione raíz", options=SHARP+FLAT, index=0)
    chord_type = st.selectbox("Tipo de acorde", options=[
        "maj","min","dim","aug","sus2","sus4","7","maj7","m7","m7b5","9","11","13"
    ], index=0)
    if st.button("Generar acorde"):
        notes = build_chord(root, chord_type, prefer_flats_for_tonic(root))
        st.write(f"**{root}{chord_type}** → Notas: {notes}")

    st.markdown("---")
    st.subheader("Identificar un acorde desde notas")
    notes_input = st.text_input("Introduce notas separadas por espacio (ej: C D G B):", value="")
    if st.button("Identificar"):
        if notes_input.strip()=="":
            st.warning("Introduce algunas notas primero.")
        else:
            toks = [normalize_note(x) for x in notes_input.split()]
            name, norm_notes = chord_name_from_notes(toks)
            st.write(f"Hipótesis: **{name}**  → Notas (template): {norm_notes}")

# --------------
# Page: Concepts / help (user-editable label)
# --------------
else:
    st.header(label_concepts)
    st.write("""
    Aquí va la ayuda básica y los colores:
    - **Rosa**: Tónicas / centros  
    - **Azul**: Relativos / modos menores  
    - **Amarillo**: Dominantes / generadores de tensión  
    - **Morado**: Disminuidos / acordes de paso
    """)
    st.write("Progresiones útiles (ejemplos):")
    st.write("- Pop: I - V - vi - IV")
    st.write("- Balada: I - IV - V - I")
    st.write("- Tensión/resolución: ii - V - I")
    st.write("- Cadena de dominantes: II7 → V7 → I")

# Footer: link to PDF (download only)
st.markdown("---")
st.markdown(f"PDF (descarga): [{PDF_LOCAL_PATH}]({PDF_LOCAL_PATH})")
st.caption("App basada en el material del PDF. Puedes pedirme que añadamos exportación MIDI, piano-roll, gráficos más detallados o pantalla de inicio personalizada.")
