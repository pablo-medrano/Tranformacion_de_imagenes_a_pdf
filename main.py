import os
import cv2
import tempfile
import re
from copy import deepcopy
from PIL import Image
from pypdf import PdfReader, PdfWriter, Transformation

# Función para modificar el nombre base de la imagen
def get_modified_basename(base_name: str) -> str:
    """
    Reemplaza la cadena "-Xn_waifu2x_noise3_scale4x" por "(n COPIAS)".
    Por ejemplo: "BT14-069-X1_waifu2x_noise3_scale4x" se transforma en "BT14-069 (1 COPIAS)".
    """
    pattern = r"-X(\d)_waifu2x_noise3_scale4x"
    modified = re.sub(pattern, r" (\1 COPIAS)", base_name)
    return modified.strip()

# ========================
# PROCESO 1: Conversión de Imágenes (sin upscaling)
# ========================
def convert_webp_to_jpg(input_path: str, output_path: str, quality: int = 90):
    """
    Convierte una imagen WEBP a JPG.
    """
    try:
        with Image.open(input_path) as img:
            rgb_im = img.convert("RGB")
            rgb_im.save(output_path, "JPEG", quality=quality)
            print(f"Convertido: {input_path} --> {output_path}")
    except Exception as e:
        print(f"Error al convertir {input_path}: {e}")

def process_images(input_folder: str, output_folder: str):
    """
    Procesa todas las imágenes (WEBP, JPG, JPEG, PNG):
      - Si la imagen es WEBP, se convierte a JPG.
      - Si es JPG, JPEG o PNG, se copia directamente.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        base, ext = os.path.splitext(filename)
        ext = ext.lower()
        input_path = os.path.join(input_folder, filename)
        if ext == ".webp":
            output_path = os.path.join(output_folder, f"{base}.jpg")
            convert_webp_to_jpg(input_path, output_path)
        elif ext in [".jpg", ".jpeg", ".png"]:
            output_path = os.path.join(output_folder, filename)
            try:
                with Image.open(input_path) as img:
                    img.convert("RGB").save(output_path)
                print(f"Copiado: {input_path} --> {output_path}")
            except Exception as e:
                print(f"Error al copiar {input_path}: {e}")

# ========================
# PROCESO 2: Conversión de Imágenes a PDF
# ========================
def get_unique_filename(folder, base_name, extension):
    """
    Genera un nombre de archivo único dentro de la carpeta.
    """
    filename = f"{base_name}{extension}"
    counter = 1
    while os.path.exists(os.path.join(folder, filename)):
        filename = f"{base_name} ({counter}){extension}"
        counter += 1
    return filename

def convert_images_to_pdf(input_folder: str, output_folder: str):
    """
    Convierte las imágenes (JPG o PNG) de la carpeta de entrada a PDF.
    Se utiliza el modelo de superresolución ESPCN x3 para mejorar la calidad.
    Además, se modifica el nombre de los archivos para sustituir la cadena especial.
    """
    os.makedirs(output_folder, exist_ok=True)

    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    model_path = "ESPCN_x3.pb"
    sr.readModel(model_path)
    sr.setModel("espcn", 3)

    for file in os.listdir(input_folder):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            base_original = os.path.splitext(file)[0]
            # Aplicar el reemplazo para modificar el nombre base
            modified_base = get_modified_basename(base_original)
            image_path = os.path.join(input_folder, file)
            img = cv2.imread(image_path)
            if img is None:
                print(f"No se pudo leer la imagen {file}.")
                continue
            enhanced_img = sr.upsample(img)
            enhanced_img_rgb = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(enhanced_img_rgb)
            
            unique_pdf_name = get_unique_filename(output_folder, modified_base, ".pdf")
            pdf_path = os.path.join(output_folder, unique_pdf_name)
            pil_image.convert('RGB').save(pdf_path)
            print(f"Guardado: {pdf_path}")

# ========================
# PROCESO 3: Corrección de Dimensiones de PDFs
# ========================
def cm_to_points(cm):
    return cm * 72 / 2.54

# Dimensiones en puntos
target_content_width = cm_to_points(6.3)
target_content_height = cm_to_points(8.8)
final_width = cm_to_points(6.7)
final_height = cm_to_points(9.2)
margin = cm_to_points(0.2)

def process_pdf(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        orig_width = float(page.mediabox.width)
        orig_height = float(page.mediabox.height)
        
        scale_x = target_content_width / orig_width
        scale_y = target_content_height / orig_height
        
        transformation = Transformation().scale(scale_x, scale_y).translate(margin, margin)
        
        new_page = writer.add_blank_page(width=final_width, height=final_height)
        transformed_page = deepcopy(page)
        transformed_page.add_transformation(transformation)
        new_page.merge_page(transformed_page)
        
    with open(output_pdf_path, "wb") as f:
        writer.write(f)
    print(f"Procesado: {os.path.basename(input_pdf_path)} -> {os.path.basename(output_pdf_path)}")

def correct_pdfs(input_folder: str, output_folder: str):
    os.makedirs(output_folder, exist_ok=True)
    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            input_pdf_path = os.path.join(input_folder, file)
            output_pdf_path = os.path.join(output_folder, file)
            process_pdf(input_pdf_path, output_pdf_path)

# ========================
# EJECUCIÓN DEL PIPELINE COMPLETO
# ========================
def main():
    print("Ejecutando el Pipeline Completo...\n")
    
    # Directorio final para los PDFs corregidos
    final_pdf_folder = os.path.join("producto_final", "pdf_corregidos")
    os.makedirs(final_pdf_folder, exist_ok=True)
    
    # Crear directorios temporales para los resultados intermedios
    with tempfile.TemporaryDirectory() as temp_transform:
        with tempfile.TemporaryDirectory() as temp_pdf:
            print(f"Directorio temporal para imágenes transformadas: {temp_transform}")
            print(f"Directorio temporal para PDF generados: {temp_pdf}")
            
            print("\n--- Proceso 1: Procesar imágenes (producto_inicio -> TEMP transformaciones) ---")
            process_images(input_folder="producto_inicio", output_folder=temp_transform)
            
            print("\n--- Proceso 2: Convertir imágenes a PDF (TEMP transformaciones -> TEMP archivos_pdf) ---")
            convert_images_to_pdf(input_folder=temp_transform, output_folder=temp_pdf)
            
            print("\n--- Proceso 3: Corrección de dimensiones de PDFs (TEMP archivos_pdf -> pdf_corregidos) ---")
            correct_pdfs(input_folder=temp_pdf, output_folder=final_pdf_folder)
    
    print("\nPipeline completado. Revisa la carpeta 'producto_final/pdf_corregidos' para ver los resultados finales.")

if __name__ == "__main__":
    main()
