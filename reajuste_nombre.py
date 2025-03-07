import os
import re

def rename_files():
    folder_path = "cambio_nombre"
    if not os.path.exists(folder_path):
        print(f"La carpeta '{folder_path}' no existe.")
        return
    
    # Patrón: captura "n COPIAS" al final, opcionalmente seguido de la extensión (por ejemplo .pdf)
    pattern = re.compile(r'(\d+ COPIAS)(\.[^.]+)?$')
    
    for filename in os.listdir(folder_path):
        print("Revisando:", filename)
        match = pattern.search(filename)
        if match:
            print("  -> Coincide!")
            # La parte "n COPIAS" y la extensión (si existe)
            new_name = pattern.sub(r'(\1)\2', filename)
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            os.rename(old_path, new_path)
            print(f"  Renombrado: {filename} -> {new_name}")
        else:
            print("  -> No coincide")

if __name__ == "__main__":
    rename_files()
