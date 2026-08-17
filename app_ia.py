import streamlit as st
import json
import os
import random
import math
from PIL import Image

# Archivos de memoria en disco (JSON)
MEMORIA_TEXTO_FILE = "memoria_texto.json"
MEMORIA_REFUERZO_FILE = "memoria_refuerzo.json"
MEMORIA_IMAGENES_FILE = "memoria_imagenes.json"

class IACompleta:
    def __init__(self):
        self.memoria_texto = self.cargar_json(MEMORIA_TEXTO_FILE)
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
        with open(MEMORIA_TEXTO_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memoria_texto, f, indent=4, ensure_ascii=False)
        with open(MEMORIA_REFUERZO_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tabla_q, f, indent=4, ensure_ascii=False)
        with open(MEMORIA_IMAGENES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memoria_imagenes, f, indent=4, ensure_ascii=False)

    # --- APRENDIZAJE Y APLICACIÓN DE TEXTO ---
    def aprender_texto(self, palabra, definicion):
        p_clean = palabra.strip().lower()
        d_clean = definicion.strip().lower()
        self.memoria_texto[p_clean] = d_clean
        self.guardar_memoria()

    def aplicar_texto(self, entrada):
        """Aplica las asociaciones aprendidas para generar una respuesta o razonar."""
        texto_clean = entrada.strip().lower()
        palabras = texto_clean.split()
        
        # 1. Modo búsqueda inversa: ¿Preguntaron por un concepto general? (Ej: "¿qué es un saludo?")
        coincidencias_concepto = []
        for palabra, definicion in self.memoria_texto.items():
            if palabra in texto_clean or definicion in texto_clean:
                coincidencias_concepto.append(f"• **{palabra}**: {definicion}")

        # 2. Generar respuesta conectando conceptos conocidos
        respuestas_directas = []
        for p in palabras:
            p_sub = p.strip(",.?!")
            if p_sub in self.memoria_texto:
                respuestas_directas.append(f"Entiendo que **'{p_sub}'** significa *{self.memoria_texto[p_sub]}*.")

        if respuestas_directas:
            return "💡 **Aplicando lo aprendido:**\n\n" + "\n".join(respuestas_directas)
        elif coincidencias_concepto:
            return "🔍 **Relacionado en memoria:**\n\n" + "\n".join(coincidencias_concepto)
        else:
            return "🤔 No tengo suficiente conocimiento para responder sobre esto. ¡Enséñame escribiendo: *palabra es definición*!"

    # --- PROCESAMIENTO Y APLICACIÓN DE IMÁGENES ---
    def extraer_patron(self, img_pil):
        img = img_pil.convert('RGB').resize((50, 50))
        pixels = list(img.getdata())
        r_total = sum(p[0] for p in pixels) / len(pixels) / 255.0
        g_total = sum(p[1] for p in pixels) / len(pixels) / 255.0
        b_total = sum(p[2] for p in pixels) / len(pixels) / 255.0
        return {"rojo": round(r_total, 3), "verde": round(g_total, 3), "azul": round(b_total, 3)}

    def aprender_imagen(self, etiqueta, img_pil):
        patron = self.extraer_patron(img_pil)
        self.memoria_imagenes[etiqueta.strip().lower()] = patron
        self.guardar_memoria()
        return patron

    def clasificar_imagen(self, img_pil):
        if not self.memoria_imagenes:
            return None, 0.0

        patron_nuevo = self.extraer_patron(img_pil)
        mejor_etiqueta = None
        menor_distancia = float('inf')

        for etiqueta, patron_guardado in self.memoria_imagenes.items():
            distancia = math.sqrt(
                (patron_nuevo["rojo"] - patron_guardado["rojo"]) ** 2 +
                (patron_nuevo["verde"] - patron_guardado["verde"]) ** 2 +
                (patron_nuevo["azul"] - patron_guardado["azul"]) ** 2
            )
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_etiqueta = etiqueta

        confianza = max(0.0, round((1.0 - menor_distancia) * 100, 1))
        return mejor_etiqueta, confianza

    # --- REFUERZO ---
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

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="IA con Aprendizaje Activo", page_icon="🤖", layout="centered")

if "ia" not in st.session_state:
    st.session_state.ia = IACompleta()

ia = st.session_state.ia

st.title("🤖 IA con Aprendizaje Activo (Texto e Imágenes)")

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Chat y Razonamiento", 
    "🖼️ Enseñar Imagen", 
    "🔍 Reconocer Imagen", 
    "🎯 Ensayo y Error"
])

# --- TAB 1: CHAT Y APLICACIÓN DE TEXTO ---
with tab1:
    st.subheader("Enseña texto o pon a prueba lo que aprendió")
    st.info("💡 **Para enseñar un concepto:** Escribe `palabra es definición` (Ejemplo: `hola es un saludo`).\n\n💬 **Para hablarle:** Escribe cualquier frase y usará su memoria para responder.")

    mensaje = st.text_input("Escribe tu mensaje:", key="input_chat")
    if st.button("Enviar Mensaje", type="primary"):
        if mensaje.strip():
            if " es " in mensaje.lower():
                partes = mensaje.lower().split(" es ", 1)
                palabra = partes[0].strip()
                definicion = partes[1].strip()
                ia.aprender_texto(palabra, definicion)
                st.success(f"¡Concepto aprendido! Guardé: **'{palabra}'** = **{definicion}**.")
            else:
                respuesta = ia.aplicar_texto(mensaje)
                st.write(respuesta)

    st.markdown("---")
    with st.expander("📖 Ver memoria de conceptos aprendidos"):
        st.json(ia.memoria_texto)

# --- TAB 2: ENSEÑAR IMAGEN ---
with tab2:
    st.subheader("1. Entrenar a la IA con una imagen")
    archivo_entrenar = st.file_uploader("Sube una foto para enseñarle:", type=["png", "jpg", "jpeg"], key="uploader_teach")
    if archivo_entrenar is not None:
        img = Image.open(archivo_entrenar)
        st.image(img, width=200)
        nombre_concepto = st.text_input("¿Qué es esta imagen? (Ej: gota_de_agua):")
        if st.button("Guardar Imagen en Memoria"):
            if nombre_concepto.strip():
                patron = ia.aprender_imagen(nombre_concepto, img)
                st.success(f"¡Aprendido! Registrado '{nombre_concepto}' con patrón RGB: {patron}")
            else:
                st.warning("Escribe el nombre del concepto.")

# --- TAB 3: RECONOCER IMAGEN ---
with tab3:
    st.subheader("2. Poner a prueba el reconocimiento visual")
    archivo_test = st.file_uploader("Sube una imagen nueva para clasificar:", type=["png", "jpg", "jpeg"], key="uploader_test")
    if archivo_test is not None:
        img_test = Image.open(archivo_test)
        st.image(img_test, width=200)
        if st.button("¿Qué imagen es esta?", type="primary"):
            prediccion, confianza = ia.clasificar_imagen(img_test)
            if prediccion:
                st.balloons()
                st.success(f"¡La IA reconoce esta imagen como: **{prediccion.upper()}**!")
                st.write(f"**Confianza:** {confianza}%")
            else:
                st.error("La memoria de imágenes está vacía.")

# --- TAB 4: REFUERZO ---
with tab4:
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
