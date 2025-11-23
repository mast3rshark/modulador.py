# modulador.py
import streamlit as st
import numpy as np
from typing import List, Tuple
import mido
from io import BytesIO

# ==============================
# CONSTANTES Y HELPERS
# ==============================
SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
TONICS_UI = ["C", "G", "D", "A", "E", "B", "F#", "C#", "Ab", "Eb", "Bb", "F",
             "Am", "Em", "Bm", "F#m", "C#m", "G#m", "Ebm", "Bbm", "Fm", "Cm", "Gm", "Dm"]

MAJOR_STEPS = [2, 2, 1, 2, 2, 2, 1]
MINOR_STEPS = [2, 1, 2, 2, 1, 2, 2]

CIRCLE_MAJOR = ["C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "Eb", "Bb", "F"]
CIRCLE_MINOR = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "Ebm", "A#m", "Fm", "Cm", "Gm", "Dm"]

def normalize_note(s: str) -> str:
    return s.strip().replace("♯", "#").replace("♭", "b")

def note_to_index(n: str) -> int:
    n = normalize_note(n)
    if n.endswith("m"): n = n[:-1]
    if n in SHARP: return SHARP.index(n)
    if n in FLAT: return FLAT.index(n)
    raise ValueError(f"Nota desconocida: {n}")

def index_to_note(i: int, flats=False) -> str:
    i = i % 12
    return FLAT[i] if flats else SHARP[i]

def prefer_flats(tonic: str) -> bool:
    flats_keys = ['F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb']
    root = tonic[:-1] if tonic.endswith('m') else tonic
    return root in flats_keys

def build_scale(tonic: str, mode: str = "major") -> List[str]:
    root = tonic[:-1] if tonic.endswith('m') else tonic
    is_minor = tonic.endswith('m') or mode == "minor"
    start = note_to_index(root)
    steps = MINOR_STEPS if is_minor else MAJOR_STEPS
    flats = prefer_flats(tonic)
    scale = []
    idx = start
    for s in steps:
        scale.append(index_to_note(idx, flats))
        idx = (idx + s) % 12
    return scale

def triad(scale: List[str], degree: int) -> List[str]:
    return [scale[(degree-1)%7], scale[(degree+1)%7], scale[(degree+3)%7]]

def seventh(scale: List[str], degree: int) -> List[str]:
    return [scale[(degree-1)%7], scale[(degree+1)%7], scale[(degree+3)%7], scale[(degree+5)%7]]

# ==============================
# ACORDES BÁSICOS
# ==============================
CHORD_TEMPLATES = {
    "maj": (0,4,7), "min": (0,3,7), "dim": (0,3,6), "aug": (0,4,8),
    "sus2": (0,2,7), "sus4": (0,5,7), "7": (0,4,7,10), "maj7": (0,4,7,11),
    "m7": (0,3,7,10), "m7b5": (0,3,6,10), "dim7": (0,3,6,9), "add9": (0,4,7,14)
}

def build_chord(root: str, ctype: str) -> List[str]:
    root_idx = note_to_index(root)
    formula = CHORD_TEMPLATES[ctype]
    flats = prefer_flats(root)
    return [index_to_note(root_idx + i, flats) for i in formula]

# ==============================
# MODULACIÓN (lo que más querés)
# ==============================
def find_pivot_chords(origin: str, target: str) -> List[Tuple[str, str]]:
    scale_o = build_scale(origin)
    scale_t = build_scale(target)
    chords_o = [triad(scale_o, i) + [""] for i in range(1,8)] + [seventh(scale_o, i) for i in range(1,8)]
    chords_t = [triad(scale_t, i) + [""] for i in range(1,8)] + [seventh(scale_t, i) for i in range(1,8)]
    
    pivots = []
    for co in chords_o:
        for ct in chords_t:
            common = set(note_to_index(n) for n in co if n) & set(note_to_index(n) for n in ct if n)
            if len(common) >= 2:
                name_o = "".join(co).replace("", "") if co[3] else "".join(co[:3])
                name_t = "".join(ct).replace("", "") if ct[3] else "".join(ct[:3])
                pivots.append((name_o, name_t))
    return list(dict.fromkeys(pivots))[:8]

# ==============================
# MIDI SIMPLE (opcional)
# ==============================
def notes_to_midi(notes: List[str]) -> BytesIO:
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    for note in notes:
        midi_note = 60 + note_to_index(note)
        track.append(mido.Message('note_on', note=midi_note, velocity=80, time=0))
        track.append(mido.Message('note_off', note=midi_note, velocity=0, time=480))
        track.append(mido.Message('note_on', note=0, velocity=0, time=240))  # pausa
    buffer = BytesIO()
    mid.save(file=buffer)
    buffer.seek(0)
    return buffer

# ==============================
# INTERFAZ STREAMLIT
# ==============================
st.set_page_config(page_title="Modulador Musical - Armonía Ilustrada", layout="wide")
st.title("Modulador Musical")
st.markdown("### Basado en *Armonía Ilustrada* de Brian Callipari – conexiones suaves entre tonalidades")

# Sidebar
page = st.sidebar.radio("Sección", [
    "Inicio",
    "Círculo de Quintas",
    "Modos & Acordes",
    "Modulación Avanzada (tu favorito)",
    "Constructor de Acordes",
    "Conceptos del Libro"
])

# ====================== INICIO ======================
if page == "Inicio":
    st.header("Bienvenido")
    st.image("https://i.imgur.com/5eM8z0K.png", use_column_width=True)  # portada del libro (link público)
    st.markdown("""
    Esta app te permite:
    - Ver el **círculo de quintas** completo
    - Construir escalas y acordes
    - **Modular sin que suene feo** (lo que más querías)
    - Todo inspirado en el libro *Armonía Ilustrada* de Brian Callipari
    """)

# ====================== CÍRCULO ======================
elif page == "Círculo de Quintas":
    st.header("Círculo de Quintas – Mayores (externo) / Menores (interno)")
    svg = '''
    <svg width="100%" height="500" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
        <defs><style>.txt{font: bold 16px Arial; text-anchor:middle; fill:white}</style></defs>
        <!-- Mayores -->
        <circle cx="200" cy="200" r="160" fill="none" stroke="#444" stroke-width="3"/>
        <!-- Menores -->
        <circle cx="200" cy="200" r="110" fill="none" stroke="#444" stroke-width="2"/>
    '''
    for i, (maj, mino) in enumerate(zip(CIRCLE_MAJOR, CIRCLE_MINOR)):
        ang = np.pi * (i / 6 - 0.5)
        # Mayor
        x1 = 200 + 160 * np.cos(ang)
        y1 = 200 + 160 * np.sin(ang)
        svg += f'<circle cx="{x1}" cy="{y1}" r="28" fill="#333"/>'
        svg += f'<text x="{x1}" y="{y1+6}" class="txt">{maj}</text>'
        # Menor
        x2 = 200 + 110 * np.cos(ang)
        y2 = 200 + 110 * np.sin(ang)
        svg += f'<circle cx="{x2}" cy="{y2}" r="22" fill="#555"/>'
        svg += f'<text x="{x2}" y="{y2+5}" style="font-size:14px; fill:#0ff">{mino}</text>'
    svg += "</svg>"
    st.markdown(svg, unsafe_allow_html=True)

# ====================== MODOS ======================
elif page == "Modos & Acordes":
    st.header("Modos y Acordes")
    tonic = st.selectbox("Tónica", TONICS_UI, index=0)
    scale = build_scale(tonic)
    st.write(f"**Escala {tonic}:** {', '.join(scale)}")
    for deg in range(1, 8):
        tri = triad(scale, deg)
        sev = seventh(scale, deg)
        st.write(f"Grado {deg}: **{tri[0]}** → {', '.join(tri)} | 7ª → {', '.join(sev)}")

# ====================== MODULACIÓN (LO QUE QUERÍAS) ======================
elif page == "Modulación Avanzada (tu favorito)":
    st.header("Modulación Suave – de una tonalidad a otra sin cortar")
    st.markdown("""
    **Del libro:** Usa puentes (acordes pivote, dominantes o sustituto tritonal)  
    para que el cambio sea natural y no suene "feo".
    """)
    
    col1, col2 = st.columns(2)
    origin = col1.selectbox("Estoy en", TONICS_UI, index=0)
    target = col2.selectbox("Quiero ir a", TONICS_UI, index=4)
    
    if st.button("¡Dame opciones de modulación!"):
        st.success(f"Modulación de **{origin}** → **{target}**")
        
        # 1. Pivotes
        pivots = find_pivot_chords(origin, target)
        if pivots:
            st.subheader("Puentes por acorde pivote (más suave)")
            for o, t in pivots:
                st.write(f"{o} → (pivote) → {t}")
        
        # 2. Dominante secundaria
        target_root = target[:-1] if target.endswith('m') else target
        dom_sec = index_to_note(note_to_index(target_root) - 5, prefer_flats(target)) + "7"
        st.subheader("Dominante secundaria")
        st.write(f"Usa **{dom_sec}** → **{target}** (clásico 2-5-1 en la nueva tonalidad)")
        
        # 3. Sustituto tritonal
        trit_root = index_to_note(note_to_index(target_root) + 6, prefer_flats(target))
        st.subheader("Sustituto tritonal (dramático pero elegante)")
        st.write(f"Usa **{trit_root}7** → **{target}** (el tritono sustituye al V7)")
        
        # 4. Ejemplo completo
        st.subheader("Progresión completa de ejemplo")
        ejemplo = f"{origin} → {pivots[0][0] if pivots else dom_sec} → {target}"
        st.code(ejemplo)
        
        # MIDI opcional
        if st.button("Descargar ejemplo como MIDI"):
            notes_example = [origin, pivots[0][0] if pivots else dom_sec, target]
            midi = notes_to_midi(notes_example)
            st.download_button("Descargar MIDI", midi, f"modulacion_{origin}_a_{target}.mid", "audio/midi")

# ====================== CONSTRUCTOR ======================
elif page == "Constructor de Acordes":
    st.header("Constructor / Identificador de Acordes")
    root = st.selectbox("Raíz", SHARP + FLAT)
    ctype = st.selectbox("Tipo", list(CHORD_TEMPLATES.keys()))
    if st.button("Construir"):
        notas = build_chord(root, ctype)
        st.write(f"**{root}{ctype}** → {', '.join(notas)}")
        if st.button("Exportar como MIDI"):
            midi = notes_to_midi(notas)
            st.download_button("Descargar acorde MIDI", midi, f"{root}{ctype}.mid")

# ====================== CONCEPTOS DEL LIBRO ======================
else:
    st.header("Conceptos del Libro – Armonía Ilustrada")
    with st.expander("Sobre el libro y el autor"):
        st.markdown("""
        **Brian Callipari** – Guitarrista y diseñador industrial argentino.  
        El libro se basa en gráficos visuales para conectar acordes sin necesidad de partitura.  
        Foco principal: **puentes y modulaciones suaves**.
        """)
    with st.expander("Tipos de modulación que usa el libro"):
        st.write("- Acorde pivote\n- Dominante secundaria\n- Sustituto tritonal\n- Cadenas de dominantes")
    with st.expander("Consejo del autor"):
        st.write("Poné dos acordes en loop (hasta los más lejanos) y creá melodías arriba. Siempre hay una conexión hermosa.")

st.caption("App creada con amor para músicos – inspirada 100% en *Armonía Ilustrada* de Brian Callipari")
