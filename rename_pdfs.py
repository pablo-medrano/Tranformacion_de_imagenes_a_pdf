import os
import re

def get_modified_basename(base_name: str) -> str:
    """
    Reemplaza la cadena "-Xn_waifu2x_noise3_scale4x" por "n COPIAS".
    Ejemplo: "BT14-069-X1_waifu2x_noise3_scale4x" se transforma en "BT14-069 1 COPIAS".
    """
    pattern = r"-X(\d)_waifu2x_noise3_scale4x"
    modified = re.sub(pattern, r" \1 COPIAS", base_name)
    return modified.strip()

def get_unique_filename(folder: str, base_name: str, extension: str) -> str:
    """
    Genera un nombre de archivo único dentro de la carpeta para evitar sobrescribir archivos.
    """
    filename = f"{base_name}{extension}"
    counter = 1
    while os.path.exists(os.path.join(folder, filename)):
        filename = f"{base_name} ({counter}){extension}"
        counter += 1
    return filename

def rename_pdfs(input_folder: str):
    """
    Recorre la carpeta dada y renombra todos los archivos PDF reemplazando la cadena
    "-Xn_waifu2x_noise3_scale4x" por "n COPIAS".
    """
    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            base, ext = os.path.splitext(file)
            new_base = get_modified_basename(base)
            if new_base != base:
                new_filename = get_unique_filename(input_folder, new_base, ext)
                old_file_path = os.path.join(input_folder, file)
                new_file_path = os.path.join(input_folder, new_filename)
                os.rename(old_file_path, new_file_path)
                print(f"Renombrado: '{file}' --> '{new_filename}'")

def main():
    # Se obtiene la ruta del directorio donde se encuentra el script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Se define la carpeta "rename" dentro de la raíz del script.
    rename_folder = os.path.join(script_dir, "rename")
    
    if not os.path.isdir(rename_folder):
        print(f"La carpeta '{rename_folder}' no existe.")
        return
    
    print(f"Procesando archivos PDF en la carpeta: {rename_folder}\n")
    rename_pdfs(rename_folder)

if __name__ == '__main__':
    main()
