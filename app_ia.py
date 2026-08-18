# 1. BORRAR UN CONCEPTO DE TEXTO:
def borrar_texto(self, palabra):
    p_clean = palabra.strip().lower()
    if p_clean in self.memoria_texto:
        del self.memoria_texto[p_clean]  # Elimina el dato del diccionario
        self.guardar_memoria()            # Guarda el cambio en el archivo JSON
        return f"Se borró '{palabra}' de la memoria."
    return "Esa palabra no existía en la memoria."

# 2. BORRAR UNA IMAGEN APRENDIDA:
def borrar_imagen(self, etiqueta):
    e_clean = etiqueta.strip().lower()
    if e_clean in self.memoria_imagenes:
        del self.memoria_imagenes[e_clean]
        self.guardar_memoria()
        return f"Se borró el patrón de '{etiqueta}'."
    return "Esa etiqueta no existe en la memoria."

# 3. REINICIAR Y BORRAR TODA LA MEMORIA POR COMPLETO:
def borrar_todo(self):
    self.memoria_texto = {}
    self.memoria_imagenes = {}
    self.tabla_q = {}
    self.guardar_memoria()
