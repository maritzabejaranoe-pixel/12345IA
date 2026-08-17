import streamlit as st
import json
import os
import random

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

    # --- TIPO 1: APRENDIZAJE POR ASOCIACIÓN / DICCIONARIO ---
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
        return "No reconozco esa palabra en mi memoria. ¡Enséñamela escribiendo: *palabra es definición*!"

    # --- TIPO 2: APRENDIZAJE POR REFUERZO ---
    def seleccionar_accion(self, estado):
        if estado not in self.tabla_q:
            self.tabla_q[estado] = {"Acción A": 0.0, "Acción B": 0.0, "Acción C": 0.0}
        acciones = self.tabla_q[estado]
        
        # 20% exploración aleatoria, 80% mejor opción aprendida
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

# --- CONFIGURACIÓN DE LA INTERFAZ WEB (STREAMLIT) ---
st.set_page_config(page_title="IA con Aprendizaje", page_icon="🤖", layout="centered")

# Guardar instancia de la IA en la sesión de la app web
if "ia" not in st.session_state:
    st.session_state.ia = IACompleta()

ia = st.session_state.ia

st.title("🤖 Sistema de IA con Aprendizaje")

tab1, tab2 = st.tabs(["💬 Chat / Diccionario", "🎯 Ensayo y Error"])

# --- PESTAÑA 1: CHAT Y CONCEPTOS ---
with tab1:
    st.subheader("Enseña o conversa con la IA")
    st.info("Para enseñarle un concepto escribe: `hola es un saludo` o `gota es agua`")

    mensaje = st.text_input("Escribe tu mensaje o enseñanza:", key="input_chat")
    
    if st.button("Enviar Mensaje", type="primary"):
        if mensaje.strip():
            if " es " in mensaje.lower():
                partes = mensaje.lower().split(" es ", 1)
                palabra = partes[0].strip()
                definicion = partes[1].strip()
                ia.aprender_texto(palabra, definicion)
                st.success(f"¡Guardado en memoria! Aprendí que **'{palabra}'** es **{definicion}**.")
            else:
                respuesta = ia.responder_texto(mensaje)
                st.write("### Respuesta de la IA:")
                st.write(respuesta)

# --- PESTAÑA 2: REFUERZO (ENSAYO Y ERROR) ---
with tab2:
    st.subheader("Entrenamiento por Refuerzo (Premios y Castigos)")

    estado_input = st.text_input("Estado actual (Situación):", value="Alguien te dice Hola")

    if st.button("¿Qué hace la IA?"):
        st.session_state.accion_elegida = ia.seleccionar_accion(estado_input)

    if "accion_elegida" in st.session_state:
        st.markdown(f"### Acción elegida: **{st.session_state.accion_elegida}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Premio (+10)", use_container_width=True):
                ia.aprender_refuerzo(estado_input, st.session_state.accion_elegida, 10)
                st.success(f"¡Premio otorgado! Puntuación de '{st.session_state.accion_elegida}' subió.")
        with col2:
            if st.button("👎 Castigo (-10)", use_container_width=True):
                ia.aprender_refuerzo(estado_input, st.session_state.accion_elegida, -10)
                st.error(f"¡Castigo aplicado! Puntuación de '{st.session_state.accion_elegida}' bajó.")

    st.markdown("---")
    st.write("#### Memoria actual de la Tabla Q:")
    st.json(ia.tabla_q)
