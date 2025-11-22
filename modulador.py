import streamlit as st
import numpy as np
from mido import Message, MidiFile, MidiTrack

############################################
# DATOS BASE
############################################
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

ESCALAS_MAYORES = {
    "C": ["C", "D", "E", "F", "G", "A", "B"],
    "C#": ["C#", "D#", "F", "F#", "G#", "A#", "C"],
    "D": ["D", "E", "F#", "G", "A", "B", "C#"],
    "D#": ["D#", "F", "G", "G#", "A#", "C", "D"],
    "E": ["E", "F#", "G#", "A", "B", "C#", "D#"],
    "F": ["F", "G", "A", "A#", "C", "D", "E"],
    "F#": ["F#", "G#", "A#", "B", "C#", "D#", "F"],
    "G": ["G", "A", "B", "C", "D", "E", "F#"],
    "G#": ["G#", "A#", "C", "C#", "D#", "F", "G"],
    "A": ["A", "B", "C#", "D", "E", "F#", "G#"],
    "A#": ["A#", "C", "D", "D#", "F", "G", "A"],
    "B": ["B", "C#", "D#", "E", "F#", "G#", "A#"]
}

GRADOS_MAYORES = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]

############################################
# Construcción de acordes
############################################
def build_chord(root, tipo):
    """Genera acordes mayores, menores, maj7 y min7."""
    index = NOTAS.index(root)

    # Interválica
    terceras = {"maj": 4, "min": 3, "maj7": 4, "min7": 3}
    septimas = {"maj7": 11, "min7": 10}

    tercera = terceras[tipo]
    quinta = 7

    notas = [
        NOTAS[(index + 0) % 12],
        NOTAS[(index + tercera) % 12],
        NOTAS[(index + quinta) % 12]
    ]

    if tipo in ["maj7", "min7"]:
        notas.append(NOTAS[(index + septimas[tipo]) % 12])

    return notas

############################################
# MIDI EXPORT
############################################
def nota_midi(nota, octava=4):
    return NOTAS.index(nota) + 12 * (octava + 1)

def export_midi(acordes, filename="modulacion.mid"):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    for acorde in acordes:
        for nota in acorde:
            track.append(Message("note_on", note=nota_midi(nota), velocity=80, time=0))
        track.append(Message("note_off", note=nota_midi(acorde[0]), velocity=80, time=480))

    mid.save(filename)
    return filename

############################################
# Opciones de modulación
############################################
def mod_pivote(t1, t2):
    escala1 = ESCALAS_MAYORES[t1]
    escala2 = ESCALAS_MAYORES[t2]

    comunes = [n for n in escala1 if n in escala2]
    if not comunes:
        return None

    pivote = comunes[0]

    return [
        (f"{t1}maj7 (I en {t1})", build_chord(t1, "maj7")),
        (f"{pivote}m7 (acorde pivote)", build_chord(pivote, "min7")),
        (f"{t2}maj7 (I en {t2})", build_chord(t2, "maj7"))
    ]

def mod_dominante(t1, t2):
    V_de_t2 = ESCALAS_MAYORES[t2][4]
    return [
        (f"{t1}maj7 (I en {t1})", build_chord(t1, "maj7")),
        (f"{V_de_t2}7 (dominante hacia {t2})", build_chord(V_de_t2, "maj7")),
        (f"{t2}maj7 (I en {t2})", build_chord(t2, "maj7"))
    ]

def mod_cromatica(t1, t2):
    paso = NOTAS[(NOTAS.index(t1) + 1) % 12]
    return [
        (f"{t1}maj (I)", build_chord(t1, "maj")),
        (f"{paso}m7 (cromático)", build_chord(paso, "min7")),
        (f"{t2}maj7 (I en {t2})", build_chord(t2, "maj7"))
    ]

############################################
# STREAMLIT UI
############################################
st.title("🎼 Modulador Armónico Profesional")

col1, col2 = st.columns(2)
t1 = col1.selectbox("Tonalidad de origen", NOTAS)
t2 = col2.selectbox("Tonalidad destino", NOTAS)

if st.button("Generar Modulaciones"):
    st.subheader("🎯 Tonalidades y grados")

    st.write(f"### {t1} mayor")
    for g, n in zip(GRADOS_MAYORES, ESCALAS_MAYORES[t1]):
        st.write(f"{g}: {n}")

    st.write(f"### {t2} mayor")
    for g, n in zip(GRADOS_MAYORES, ESCALAS_MAYORES[t2]):
        st.write(f"{g}: {n}")

    st.divider()
    st.subheader("🎵 Opciones de modulación")

    opciones = [
        ("Modulación por acorde pivote", mod_pivote(t1, t2)),
        ("Dominante secundaria hacia la nueva tonalidad", mod_dominante(t1, t2)),
        ("Modulación cromática", mod_cromatica(t1, t2)),
    ]

    for titulo, progresion in opciones:
        if progresion:
            st.markdown(f"## 🔹 {titulo}")

            acordes_solo = []

            for nombre, notas in progresion:
                st.write(f"**{nombre}:** {notas}")
                acordes_solo.append(notas)

            if st.button(f"Exportar '{titulo}' como MIDI"):
                archivo = export_midi(acordes_solo, f"{titulo}.mid")
                with open(archivo, "rb") as f:
                    st.download_button("Descargar MIDI", f, file_name=f"{titulo}.mid")
