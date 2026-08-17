import streamlit as st
import json
import os
import random
from PIL import Image

# Archivos de memoria en disco (JSON)
MEMORIA_TEXTO_FILE = "memoria_texto.json"
MEMORIA_REFUERZO_FILE = "memoria_refuerzo.json"

class IACompleta:
    def __init__(self):
        self.memoria_texto = self.cargar_json(MEMORIA_TEXTO_FILE)
        self.tabla_q = self.cargar_json(MEMORIA_REFUERZO_FILE)
        self.tasa_aprendizaje = 0.5

    def cargar_json(self, ruta):
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_memoria(self):
        with open(MEMORIA_TEXTO_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memoria_texto, f, indent=4, ensure_ascii=False)
        with open(MEMORIA_REFUERZO_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tabla_q, f, indent=4, ensure_ascii=False)

    # --- TIPO 1: TEXTO Y CONCEPTOS ---
    def aprender_texto(self, palabra, definicion):
        self.memoria_texto[palabra.strip().lower()] = definicion
        self.guardar_memoria()

    def responder_texto(self, texto):
        palabras = texto.lower().split()
        respuestas = []
        for p in palabras:
            p_clean = p.strip(",.?!")
            if p_clean in self.memoria_texto:
                respuestas.append(f"**{p_clean}**: {self.memoria_texto[p_clean]}")
        
        if respuestas:
            return "\n\n".join(respuestas)
        return "No reconozco esa palabra. ¡Enséñamela escribiendo: *palabra es definición*!"

    # --- PROCESAMIENTO DE IMÁGENES (PillOW) ---
    def procesar_imagen(self, img_pil):
        img = img_pil.convert('RGB').resize((50, 50))
        pixels = list(img.getdata())
        r_total = round(sum(p[0] for p in pixels) / len(pixels) / 255.0, 2)
        g_total = round(sum(p[1] for p in pixels) / len(pixels) / 255.0, 2)
        b_total = round(sum(p[2] for p in pixels) / len(pixels) / 255.0, 2)
        return {"rojo": r_total, "verde": g_total, "azul": b_total}

    # --- TIPO 2: REFUERZO ---
    def seleccionar_accion(self, estado):
        if estado not in self.tabla_q:
            self.tabla_q[estado] = {"Acción A": 0.0, "Acción B": 0.0, "Acción C": 0.0}
        acciones = self.tabla_q[estado]
        if random.random() < 0.2:
            return random.choice(list(acciones.keys()))
        return max(acciones, key=acciones.get)

    def aprender_refuerzo(self, estado, accion, recompensa):
        if estado not in self.tabla_q:
            self.tabla_q[estado] = {accion: 0.0}
        val_q = self.tabla_q[estado].get(accion, 0.0)
        nuevo_val = val_q + self.tasa_aprendizaje * (recompensa - val_q)
        self.tabla_q[estado][accion] = round(nuevo_val, 4)
        self.guardar_memoria()

# --- CONFIGURACIÓN DE STREAMLIT ---
st.set_page_config(page_title="IA con Aprendizaje", page_icon="🤖", layout="centered")

if "ia" not in st.session_state:
    st.session_state.ia = IACompleta()

ia = st.session_state.ia

st.title("🤖 Sistema de IA con Aprendizaje")

tab1, tab2, tab3 = st.tabs(["💬 Chat / Diccionario", "🖼️ Aprender Imagen", "🎯 Ensayo y Error"])

# --- TAB 1: CHAT ---
with tab1:
    st.subheader("Enseña o conversa con la IA")
    st.info("Para enseñarle un concepto escribe: `hola es un saludo` o `gota es agua`")

    mensaje = st.text_input("Escribe tu mensaje o enseñanza:", key="input_chat")
    if st.button("Enviar Mensaje", type="primary"):
        if mensaje.strip():
            if " es " in mensaje.lower():
                partes = mensaje.lower().split(" es ", 1)
                ia.aprender_texto(partes[0].strip(), partes[1].strip())
                st.success(f"¡Guardado! Aprendí que **'{partes[0].strip()}'** es **{partes[1].strip()}**.")
            else:
                respuesta = ia.responder_texto(mensaje)
                st.write("### Respuesta de la IA:")
                st.write(respuesta)

# --- TAB 2: APRENDER IMÁGENES ---
with tab3:
    pass

with tab2:
    st.subheader("Extraer datos de imágenes")
    archivo_imagen = st.file_uploader("Sube una imagen (PNG o JPG):", type=["png", "jpg", "jpeg"])
    
    if archivo_imagen is not None:
        imagen = Image.open(archivo_imagen)
        st.image(imagen, caption="Imagen cargada", width=250)
        
        etiqueta = st.text_input("¿Qué representa la imagen? (Ej: gota_de_agua):")
        if st.button("Guardar Patrón Visual"):
            if etiqueta.strip():
                patron = ia.procesar_imagen(imagen)
                ia.aprender_texto(etiqueta.strip(), f"Patrón de colores extraído: {patron}")
                st.success(f"¡Guardado! La imagen de '{etiqueta}' se analizó con patrón {patron}.")
            else:
                st.warning("Escribe una etiqueta o nombre para la imagen.")

# --- TAB 3: REFUERZO ---
with tab3:
    st.subheader("Entrenamiento por Refuerzo")
    estado_input = st.text_input("Estado actual:", value="Alguien te dice Hola")

    if st.button("¿Qué hace la IA?"):
        st.session_state.accion_elegida = ia.seleccionar_accion(estado_input)

    if "accion_elegida" in st.session_state:
        st.markdown(f"### Acción elegida: **{st.session_state.accion_elegida}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Premio (+10)", use_container_width=True):
                ia.aprender_refuerzo(estado_input, st.session_state.accion_elegida, 10)
                st.success("¡Premio guardado!")
        with col2:
            if st.button("👎 Castigo (-10)", use_container_width=True):
                ia.aprender_refuerzo(estado_input, st.session_state.accion_elegida, -10)
                st.error("¡Castigo guardado!")
