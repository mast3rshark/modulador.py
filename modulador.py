import streamlit as st

# ------------------------------------------
# DATOS MUSICALES
# ------------------------------------------

NOTAS = ["C", "G", "D", "A", "E", "B", "F#", "C#", 
         "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"]

# Escalas mayores (números = semitonos)
INTERVALOS_MAYOR = [2, 2, 1, 2, 2, 2, 1]
INTERVALOS_MENOR = [2, 1, 2, 2, 1, 2, 2]

# Acordes diatónicos mayores
ACORDES_MAYOR = ["I (Maj7)", "ii (m7)", "iii (m7)", "IV (Maj7)", "V (7)", "vi (m7)", "vii° (m7b5)"]

# Acordes diatónicos menores
ACORDES_MENOR = ["i (m7)", "ii° (m7b5)", "III (Maj7)", "iv (m7)", "v (m7)", "VI (Maj7)", "VII (7)"]

# Modos griegos mayor
MODOS_MAYOR = [
    "Jónico (Ionian)",
    "Dórico (Dorian)",
    "Frigio (Phrygian)",
    "Lidio (Lydian)",
    "Mixolidio (Mixolydian)",
    "Eólico (Aeolian)",
    "Locrio (Locrian)"
]

# Modos griegos menor (rotación natural)
MODOS_MENOR = [
    "Eólico (Aeolian)",
    "Locrio (Locrian)",
    "Jónico (Ionian)",
    "Dórico (Dorian)",
    "Frigio (Phrygian)",
    "Lidio (Lydian)",
    "Mixolidio (Mixolydian)"
]

# ------------------------------------------
# FUNCIONES
# ------------------------------------------

def construir_escala(tonica, intervalos):
    notas = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    idx = notas.index(tonica.replace("b", "#"))
    escala = [tonica]

    for i in intervalos:
        idx = (idx + i) % 12
        escala.append(notas[idx])

    return escala[:-1]


def relativa(tonalidad, tipo):
    idx = NOTAS.index(tonalidad)
    if tipo == "Mayor":
        return NOTAS[(idx + 9) % len(NOTAS)]  # 6to grado
    if tipo == "Menor":
        return NOTAS[(idx + 3) % len(NOTAS)]  # 3er grado


def posicion_circulo_quintas(tonal):
    return NOTAS.index(tonal)


# ------------------------------------------
# INTERFAZ STREAMLIT
# ------------------------------------------

st.title("🎵 Asistente Musical — Círculo de Quintas + Modulación + Modos + Acordes")
st.write("Herramienta musical avanzada para estudiar tonalidades, acordes, modos griegos y modulaciones.")

st.subheader("1️⃣ Selecciona tu tonalidad inicial")
tonica = st.selectbox("Tonalidad:", NOTAS)
tipo = st.radio("Tipo:", ["Mayor", "Menor"])

# Construir escala
intervalos = INTERVALOS_MAYOR if tipo == "Mayor" else INTERVALOS_MENOR
escala = construir_escala(tonica, intervalos)

# Relativa
rel = relativa(tonica, tipo)

st.write(f"### 🎶 Escala de **{tonica} {tipo}**")
st.write("Notas:", escala)

st.write(f"**Relativa:** {rel}")

# Acordes diatónicos
st.write("### 🎼 Acordes diatónicos")
acordes = ACORDES_MAYOR if tipo == "Mayor" else ACORDES_MENOR
for grado, acorde in zip(escala, acordes):
    st.write(f"- {grado}: {acorde}")

# Modos griegos
st.write("### 🧙 Modos griegos (relacionados con esta escala)")

modos = MODOS_MAYOR if tipo == "Mayor" else MODOS_MENOR
for i in range(7):
    st.write(f"{modos[i]} → Inicia en: {escala[i]}")

# Ubicación en el círculo de quintas
st.write("### 🔄 Ubicación en el círculo de quintas")
pos = posicion_circulo_quintas(tonica)
st.write(f"Posición: {pos} de 14 (0 = C)")

# ------------------------------------------
# SECCIÓN DE MODULACIÓN
# ------------------------------------------

st.subheader("2️⃣ ¿Deseas modular a otra tonalidad?")

modular = st.checkbox("Activar modulación")

if modular:
    destino = st.selectbox("¿A qué tonalidad deseas ir?", NOTAS)
    tipo_destino = st.radio("Tipo de la tonalidad destino:", ["Mayor", "Menor"])

    pos_dest = posicion_circulo_quintas(destino)

    distancia = pos_dest - pos

    st.write("### 🎯 Modulación")
    st.write(f"De **{tonica} {tipo}** → **{destino} {tipo_destino}**")

    if distancia == 0:
        st.success("Estás en la misma tonalidad.")
    elif abs(distancia) == 1:
        st.info("Modulación cercana por el círculo de quintas (muy suave).")
    elif abs(distancia) <= 3:
        st.warning("Modulación moderada (requiere pivotes adecuados).")
    else:
        st.error("Modulación lejana (necesita cambio fuerte de acordes).")

    st.write(f"Distancia en el círculo de quintas: **{distancia} pasos**")

    st.write("### 🔑 Acordes pivote sugeridos:")
    st.write("- IV → V destino")
    st.write("- ii → V destino")
    st.write("- vii° → I destino")
    st.write("- Usar dominante secundario: V7/V destino")
