import streamlit as st
import json
import os
import random
from PIL import Image

# Archivos de memoria
MEMORIA_TEXTO_FILE = "memoria_texto.json"
MEMORIA_REFUERZO_FILE = "memoria_refuerzo.json"

class IACompleta:
    def __init__(self):
        self.memoria_texto = self.cargar_json(MEMORIA_TEXTO_FILE)
        self.tabla_q = self.cargar_json(MEMORIA_REFUERZO_FILE)
        self.tasa_aprendizaje = 0.5
        self.descuento = 0.9

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

    # --- APRENDIZAJE 1: TEXTO Y CONCEPTOS ---
    def aprender_texto(self, palabra, definicion):
        palabra_clean = palabra.strip().lower()
        self.memoria_texto[palabra_clean] = definicion
        self.guardar_memoria()
        return f"Aprendido: '{palabra}' -> {definicion}"

    def responder_texto(self, texto):
        palabras = texto.lower().split()
        respuestas = []
        for p in palabras:
            p_clean = p.strip(",.?!")
            if p_clean in self.memoria_texto:
                respuestas.append(f"• **{p_clean}**: {self.memoria_texto[p_clean]}")
        
        if respuestas:
            return "\n".join(respuestas)
        return "No reconozco ninguna palabra de tu mensaje. ¡Puedes enseñármela!"

    # --- APRENDIZAJE 2: PROCESAMIENTO DE IMÁGENES ---
    def procesar_imagen(self, ruta_imagen):
        """Extrae el color promedio (RGB) de una imagen para usarlo como patrón."""
        img = Image.open(ruta_imagen).convert('RGB')
        img = img.resize((50, 50))
        pixels = list(img.getdata())
        
        r_total = sum(p[0] for p in pixels) / len(pixels) / 255.0
        g_total = sum(p[1] for p in pixels) / len(pixels) / 255.0
        b_total = sum(p[2] for p in pixels) / len(pixels) / 255.0
        
        return {"rojo": round(r_total, 2), "verde": round(g_total, 2), "azul": round(b_total, 2)}

    # --- APRENDIZAJE 3: REFUERZO ---
    def seleccionar_accion(self, estado):
        if estado not in self.tabla_q:
            self.tabla_q[estado] = {"Acción A": 0.0, "Acción B": 0.0, "Acción C": 0.0}
        acciones = self.tabla_q[estado]
        return max(acciones, key=acciones.get)

    def aprender_refuerzo(self, estado, accion, recompensa):
        if estado not in self.tabla_q:
            self.tabla_q[estado] = {accion: 0.0}
        val_q = self.tabla_q[estado].get(accion, 0.0)
        nuevo_val = val_q + self.tasa_aprendizaje * (recompensa - val_q)
        self.tabla_q[estado][accion] = round(nuevo_val, 4)
        self.guardar_memoria()


# ==========================================
# INTERFAZ GRÁFICA CON TKINTER
# ==========================================
class AppIA:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de IA con Aprendizaje")
        self.root.geometry("600x500")

        self.ia = IACompleta()

        # Pestañas
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self.tab_chat = ttk.Frame(notebook)
        self.tab_imagen = ttk.Frame(notebook)
        self.tab_refuerzo = ttk.Frame(notebook)

        notebook.add(self.tab_chat, text="Chat / Diccionario")
        notebook.add(self.tab_imagen, text="Aprender Imagen")
        notebook.add(self.tab_refuerzo, text="Ensayo y Error")

        self.setup_tab_chat()
        self.setup_tab_imagen()
        self.setup_tab_refuerzo()

    # --- TAB CHAT / DICCIONARIO ---
    def setup_tab_chat(self):
        lbl_inst = ttk.Label(self.tab_chat, text="Conversa o enseña (Ej: 'hola es un saludo para iniciar conversa')")
        lbl_inst.pack(pady=5)

        self.txt_chat = tk.Text(self.tab_chat, height=15, state="disabled")
        self.txt_chat.pack(fill="both", expand=True, padx=10, pady=5)

        frame_input = ttk.Frame(self.tab_chat)
        frame_input.pack(fill="x", padx=10, pady=5)

        self.entry_msg = ttk.Entry(frame_input)
        self.entry_msg.pack(side="left", fill="x", expand=True)
        self.entry_msg.bind("<Return>", lambda event: self.enviar_mensaje())

        btn_send = ttk.Button(frame_input, text="Enviar", command=self.enviar_mensaje)
        btn_send.pack(side="right", padx=5)

    def enviar_mensaje(self):
        msg = self.entry_msg.get().strip()
        if not msg:
            return

        self.log_chat(f"Tú: {msg}")

        # Detectar patrón de enseñanza: "X es Y"
        if " es " in msg.lower():
            partes = msg.lower().split(" es ", 1)
            palabra = partes[0].strip()
            definicion = partes[1].strip()
            res = self.ia.aprender_texto(palabra, definicion)
            self.log_chat(f"IA: ¡Entendido! {res}")
        else:
            res = self.ia.responder_texto(msg)
            self.log_chat(f"IA: {res}")

        self.entry_msg.delete(0, tk.END)

    def log_chat(self, texto):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert(tk.END, texto + "\n\n")
        self.txt_chat.config(state="disabled")
        self.txt_chat.see(tk.END)

    # --- TAB IMAGEN ---
    def setup_tab_imagen(self):
        btn_cargar = ttk.Button(self.tab_imagen, text="Cargar Foto (ej: Gota de agua)", command=self.cargar_imagen)
        btn_cargar.pack(pady=10)

        self.lbl_img_path = ttk.Label(self.tab_imagen, text="No se ha seleccionado imagen.")
        self.lbl_img_path.pack(pady=5)

        frame_etiqueta = ttk.Frame(self.tab_imagen)
        frame_etiqueta.pack(pady=10)

        ttk.Label(frame_etiqueta, text="¿Qué representa la imagen?:").pack(side="left")
        self.entry_etiqueta = ttk.Entry(frame_etiqueta)
        self.entry_etiqueta.pack(side="left", padx=5)

        btn_guardar_img = ttk.Button(self.tab_imagen, text="Guardar en Memoria", command=self.guardar_imagen_memoria)
        btn_guardar_img.pack(pady=10)

        self.lbl_res_img = ttk.Label(self.tab_imagen, text="")
        self.lbl_res_img.pack(pady=10)

    def cargar_imagen(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.png *.jpg *.jpeg")])
        if ruta:
            self.ruta_img_actual = ruta
            self.lbl_img_path.config(text=f"Seleccionado: {os.path.basename(ruta)}")

    def guardar_imagen_memoria(self):
        if hasattr(self, 'ruta_img_actual') and self.entry_etiqueta.get():
            etiqueta = self.entry_etiqueta.get().strip()
            rasgos = self.ia.procesar_imagen(self.ruta_img_actual)
            self.ia.aprender_texto(etiqueta, f"Patrón de color extraído: {rasgos}")
            self.lbl_res_img.config(text=f"¡Imagen asociada a '{etiqueta}' con éxito!")
        else:
            messagebox.showwarning("Atención", "Carga una imagen y escribe su nombre o etiqueta.")

    # --- TAB REFUERZO ---
    def setup_tab_refuerzo(self):
        frame_ref = ttk.Frame(self.tab_refuerzo)
        frame_ref.pack(pady=20)

        ttk.Label(frame_ref, text="Estado actual:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_estado = ttk.Entry(frame_ref)
        self.entry_estado.insert(0, "Frente al fuego")
        self.entry_estado.grid(row=0, column=1, padx=5, pady=5)

        btn_decidir = ttk.Button(frame_ref, text="¿Qué hace la IA?", command=self.decidir_accion)
        btn_decidir.grid(row=1, column=0, columnspan=2, pady=10)

        self.lbl_accion = ttk.Label(self.tab_refuerzo, text="Acción: ---", font=("Arial", 12, "bold"))
        self.lbl_accion.pack(pady=10)

        frame_botones = ttk.Frame(self.tab_refuerzo)
        frame_botones.pack(pady=10)

        btn_premio = ttk.Button(frame_botones, text="👍 Premio (+10)", command=lambda: self.retroalimentar(+10))
        btn_premio.pack(side="left", padx=10)

        btn_castigo = ttk.Button(frame_botones, text="👎 Castigo (-10)", command=lambda: self.retroalimentar(-10))
        btn_castigo.pack(side="right", padx=10)

    def decidir_accion(self):
        estado = self.entry_estado.get().strip()
        self.accion_actual = self.ia.seleccionar_accion(estado)
        self.lbl_accion.config(text=f"Acción elegida: {self.accion_actual}")

    def retroalimentar(self, recompensa):
        if hasattr(self, 'accion_actual'):
            estado = self.entry_estado.get().strip()
            self.ia.aprender_refuerzo(estado, self.accion_actual, recompensa)
            messagebox.showinfo("Aprendizaje", f"Se aplicó {'Premio' if recompensa > 0 else 'Castigo'} a '{self.accion_actual}'.")
        else:
            messagebox.showwarning("Atención", "Haz clic primero en '¿Qué hace la IA?'")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppIA(root)
    root.mainloop()
