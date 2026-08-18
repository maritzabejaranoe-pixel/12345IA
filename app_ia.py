import streamlit as st
import json
import os
import random
import math
from PIL import Image
import pytesseract  # Librería para LEER texto dentro de imágenes (OCR)

# Archivos de memoria
MEMORIA_CREENCIAS_FILE = "memoria_creencias.json"
MEMORIA_REFUERZO_FILE = "memoria_refuerzo.json"
MEMORIA_IMAGENES_FILE = "memoria_imagenes.json"

class IARazonable:
    def __init__(self):
        self.creencias = self.cargar_json(MEMORIA_CREENCIAS_FILE)
        self.tabla_q = self.cargar_json(MEMORIA_REFUERZO_FILE)
        self.memoria_imagenes = self.cargar_json(MEMORIA_IMAGENES_FILE)
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
        with open(MEMORIA_CREENCIAS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.creencias, f, indent=4, ensure_ascii=False)
        with open(MEMORIA_REFUERZO_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tabla_q, f, indent=4, ensure_ascii=False)
        with open(MEMORIA_IMAGENES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memoria_imagenes, f, indent=4, ensure_ascii=False)

    # --- 1. RAZONAMIENTO Y CREENCIA PROPIA ---
    def evaluar_y_aprender(self, concepto, definicion):
        """La IA evalúa la información antes de decidir si cree en ella."""
        c_clean = concepto.strip().lower()
        d_clean = definicion.strip().lower()

        if c_clean in self.creencias:
            datos_previos = self.creencias[c_clean]
            # Si la definición coincide con lo que ya comprobó antes, aumenta su certeza
            if datos_previos["definicion"] == d_clean:
                datos_previos["comprobaciones"] += 1
                datos_previos["certeza"] = min(100, datos_previos["certeza"] + 15)
                self.guardar_memoria()
                return f"🧠 **La IA dice:** 'Ya he comprobado esto {datos_previos['comprobaciones']} veces. Estoy {datos_previos['certeza']}% segura de que **{c_clean}** es {d_clean}'."
            else:
                # Si le dices algo distinto a lo que sabe, duda
                return f"🤔 **La IA duda:** 'Tú me dices que **{c_clean}** es *{d_clean}*, pero según mis comprobaciones previas creo que es *{datos_previos['definicion']}* (Certeza: {datos_previos['certeza']}%). Necesito más pruebas.'"
        else:
            # Nuevo dato: empieza con una certeza inicial baja (40%) porque aún no lo ha comprobado sola
            self.creencias[c_clean] = {
                "definicion": d_clean,
                "certeza": 40,
                "comprobaciones": 1
            }
            self.guardar_memoria()
            return f"📝 **La IA registra la hipótesis:** 'Guardé que **{c_clean}** podría ser *{d_clean}*. Mi certeza actual es del 40% hasta que lo compruebe en el entorno.'"

    def razonar_respuesta(self, mensaje):
        """Responde basándose ÚNICAMENTE en lo que ella cree y ha verificado."""
        palabras = mensaje.lower().split()
        respuestas = []

        for p in palabras:
            p_clean = p.strip(",.?!")
            if p_clean in self.creencias:
                info = self.creencias[p_clean]
                if info["certeza"] >= 70:
                    respuestas.append(f"• Sé con alta certeza ({info['certeza']}%) que **'{p_clean}'** es *{info['definicion']}*.")
                else:
                    respuestas.append(f"• Tengo la hipótesis ({info['certeza']}% de certeza) de que **'{p_clean}'** podría ser *{info['definicion']}*.")

        if respuestas:
            return "💡 **Conclusiones propias de la IA basadas en su memoria:**\n\n" + "\n".join(respuestas)
        return "🤷 **La IA dice:** 'No tengo conocimientos ni comprobaciones previas sobre las palabras de tu mensaje.'"

    # --- 2. LECTURA DE TEXTO EN FOTOS (OCR) ---
    def leer_texto_de_imagen(self, img_pil):
        """Extrae el texto escrito dentro de una foto usando Tesseract OCR."""
        try:
            texto_extraido = pytesseract.image_to_string(img_pil, lang='spa+eng')
            return texto_extraido.strip()
        except Exception as e:
            return f"Error al procesar la imagen con OCR: {e}. Asegúrate de tener Tesseract instalado."

    # --- 3. REFUERZO ---
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

# --- INTERFAZ EN STREAMLIT ---
st.set_page_config(page_title="IA con Razonamiento Propio y OCR", page_icon="🧠", layout="centered")

if "ia" not in st.session_state:
    st.session_state.ia = IARazonable()

ia = st.session_state.ia

st.title("🧠 IA con Criterio Propio y Lectura de Fotos")

tab1, tab2, tab3 = st.tabs([
    "💬 Chat / Criterio Propio", 
    "📄 Leer Texto de Foto (OCR)", 
    "🎯 Ensayo y Error"
])

# --- TAB 1: CHAT Y CRITERIO PROPIO ---
with tab1:
    st.subheader("Conversa o propone hipótesis a la IA")
    st.info("💡 Si le enseñas algo (`concepto es definición`), la IA evaluará su nivel de certeza en lugar de repetirlo a ciegas.")

    mensaje = st.text_input("Escribe tu mensaje o enseñanza:", key="input_chat")
    if st.button("Enviar", type="primary"):
        if mensaje.strip():
            if " es " in mensaje.lower():
                partes = mensaje.lower().split(" es ", 1)
                res = ia.evaluar_y_aprender(partes[0].strip(), partes[1].strip())
                st.write(res)
            else:
                respuesta = ia.razonar_respuesta(mensaje)
                st.write(respuesta)

    st.markdown("---")
    with st.expander("📖 Ver sistema de creencias y certeza de la IA"):
        st.json(ia.creencias)

# --- TAB 2: LECTURA DE FOTOS (OCR) ---
with tab2:
    st.subheader("Extraer y leer texto desde una foto")
    archivo_foto = st.file_uploader("Sube la foto de un documento, cartel o libro:", type=["png", "jpg", "jpeg"])
    
    if archivo_foto is not None:
        img = Image.open(archivo_foto)
        st.image(img, width=300, caption="Foto cargada")
        
        if st.button("📖 Leer texto de la imagen", type="primary"):
            texto_detectado = ia.leer_texto_de_imagen(img)
            if texto_detectado:
                st.success("¡Texto detectado con éxito!")
                st.text_area("Resultado de la lectura:", value=texto_detectado, height=150)
                
                # Opción para que la IA procese lo que acaba de leer
                if st.button("🧠 Hacer que la IA analice este texto"):
                    res = ia.razonar_respuesta(texto_detectado)
                    st.write(res)
            else:
                st.warning("No se detectó texto claro en la imagen.")

# --- TAB 3: REFUERZO ---
with tab3:
    st.subheader("Entrenamiento por Refuerzo")
    estado_input = st.text_input("Estado actual:", value="Situación desconocida")
    if st.button("¿Qué hace la IA?"):
        st.session_state.accion_elegida = ia.seleccionar_accion(estado_input)

    if "accion_elegida" in st.session_state:
        st.write(f"### Acción elegida: **{st.session_state.accion_elegida}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Premio (+10)", use_container_width=True):
                ia.aprender_refuerzo(estado_input, st.session_state.accion_elegida, 10)
                st.success("¡Acción respaldada con premio!")
        with col2:
            if st.button("👎 Castigo (-10)", use_container_width=True):
                ia.aprender_refuerzo(estado_input, st.session_state.accion_elegida, -10)
                st.error("¡Acción rechazada con castigo!")
