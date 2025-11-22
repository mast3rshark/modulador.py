import streamlit as st
from mido import Message, MidiFile, MidiTrack
import io

# ---------------------------
# Utilidades musicales básicas
# ---------------------------

NOTAS = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
}

GRAUS = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]

PROGRESIONES_TIPICAS = {
    "Pop/Rock": ["I - V - vi - IV", "I - vi - IV - V", "vi - IV - I - V"],
    "Balada": ["I - IV - V - I", "I - iii - IV - V"],
    "Tensión → Resolución": ["ii - V - I", "iii - vi - ii - V - I"],
}

ACORDES_PASO = [
    "bIII", "bVI", "bVII", "#iv°", "#V°", "ii° paso", "V/V"
]

# ---------------------------
# Función para convertir acordes a MIDI
# ---------------------------

def acordes_a_midi(acordes, tempo=500000):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(Message('program_change', program=0, time=0))

    for acorde in acordes:
        if acorde not in NOTAS:
            continue

        nota_base = NOTAS[acorde] + 60  # octave 5

        notas = [nota_base, nota_base + 4, nota_base + 7]

        for n in notas:
            track.append(Message('note_on', note=n, velocity=80, time=0))

        for n in notas:
            track.append(Message('note_off', note=n, velocity=80, time=480))

    buffer = io.BytesIO()
    mid.save(buffer)
    buffer.seek(0)
    return buffer

# ---------------------------
# APP STREAMLIT
# ---------------------------

st.title("🎵 Generador de Progresiones y Exportador MIDI")
st.write("Herramienta para ayudarte a crear ideas musicales rápido.")

# 1. Preguntar tonalidad
tonalidad = st.selectbox("Selecciona la tonalidad:", list(NOTAS.keys()))

# 2. Preguntar hacia dónde quieres ir
objetivo = st.selectbox(
    "¿Qué sensación buscas?",
    ["Feliz / brillante", "Triste / melancólica", "Oscura / misteriosa", "Tensión → resolución"]
)

# 3. Sugerir progresiones
st.subheader("Progresiones sugeridas:")

if objetivo == "Feliz / brillante":
    sugerencia = PROGRESIONES_TIPICAS["Pop/Rock"]
elif objetivo == "Triste / melancólica":
    sugerencia = PROGRESIONES_TIPICAS["Balada"]
else:
    sugerencia = PROGRESIONES_TIPICAS["Tensión → Resolución"]

prog = st.radio("Elige una progresión que te guste:", sugerencia)

# 4. Acordes de paso
st.subheader("Acordes de paso opcionales:")
acordes_paso_elegidos = st.multiselect("Añadir acorde(s) de paso:", ACORDES_PASO)

# 5. Confirmación
if st.button("Generar progresión final"):
    st.success("Progresión seleccionada:")
    st.write("Progresión base:", prog)
    st.write("Acordes de paso:", acordes_paso_elegidos if acordes_paso_elegidos else "Ninguno")

# 6. Exportar MIDI
st.subheader("Exportar MIDI")

acordes_simples = ["C", "F", "G", "Am"]  # demo temporal (luego lo hacemos dinámico)

if st.button("Exportar en MIDI"):
    midi_buffer = acordes_a_midi(acordes_simples)
    st.download_button(
        label="Descargar archivo MIDI",
        data=midi_buffer,
        file_name="progresion.mid",
        mime="audio/midi"
    )
    st.success("MIDI generado correctamente.")
