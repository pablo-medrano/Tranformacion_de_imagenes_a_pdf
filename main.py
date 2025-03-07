import os
import cv2
import torch
from copy import deepcopy
from PIL import Image
from realesrgan import RealESRGANer
from pypdf import PdfReader, PdfWriter, Transformation

# ========================
# PROCESO 1: Conversión y Upscaling de Imágenes
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

def upscale_image(input_path: str, output_path: str, scale: int = 4):
    """
    Realiza un upscaling de la imagen usando Real-ESRGANer.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = RealESRGANer(
            device=device,
            scale=scale,
            model_path=f"RealESRGAN_x{scale}plus.pth",
            half=True  # usa half precision si está disponible
        )
        img = Image.open(input_path).convert("RGB")
        sr_image, _ = model.enhance(img, outscale=scale)
        sr_image.save(output_path)
        print(f"Escalado: {input_path} --> {output_path}")
    except Exception as e:
        print(f"Error al escalar {input_path}: {e}")

def process_images(input_folder: str = "producto_inicio", 
                   output_folder: str = "producto_final/transformaciones"):
    """
    Procesa todas las imágenes (WEBP, JPG, JPEG, PNG):
      - Si la imagen es WEBP, se convierte a JPG.
      - Aplica upscaling a la imagen.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        base, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in [".webp", ".jpg", ".jpeg", ".png"]:
            input_path = os.path.join(input_folder, filename)
            # Si es WEBP se convierte a JPG
            if ext == ".webp":
                temp_jpg = os.path.join(output_folder, f"{base}.jpg")
                convert_webp_to_jpg(input_path, temp_jpg)
                source_for_upscale = temp_jpg
            else:
                source_for_upscale = input_path
            final_path = os.path.join(output_folder, f"{base}_upscaled.jpg")
            upscale_image(source_for_upscale, final_path)

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

def convert_images_to_pdf(input_folder: str = "producto_final/transformaciones", 
                          output_folder: str = "producto_final/archivos_pdf"):
    """
    Convierte las imágenes (JPG o PNG) de la carpeta de entrada a PDF usando un modelo de superresolución.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Cargar modelo de superresolución (ESPCN x3)
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    model_path = "ESPCN_x3.pb"
    sr.readModel(model_path)
    sr.setModel("espcn", 3)

    for file in os.listdir(input_folder):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            base_original = os.path.splitext(file)[0]
            image_path = os.path.join(input_folder, file)
            img = cv2.imread(image_path)
            if img is None:
                print(f"No se pudo leer la imagen {file}.")
                continue
            enhanced_img = sr.upsample(img)
            enhanced_img_rgb = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(enhanced_img_rgb)
            
            unique_pdf_name = get_unique_filename(output_folder, base_original, ".pdf")
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

def correct_pdfs(input_folder: str = "producto_final/archivos_pdf", 
                 output_folder: str = "producto_final/pdf_corregidos"):
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
    
    print("--- Proceso 1: Procesar imágenes (producto_inicio -> producto_final/transformaciones) ---")
    process_images()
    
    print("\n--- Proceso 2: Convertir imágenes a PDF (producto_final/transformaciones -> producto_final/archivos_pdf) ---")
    convert_images_to_pdf()
    
    print("\n--- Proceso 3: Corregir dimensiones de PDFs (producto_final/archivos_pdf -> producto_final/pdf_corregidos) ---")
    correct_pdfs()
    
    print("\nPipeline completado. Revisa la carpeta 'producto_final' para ver los resultados finales.")

if __name__ == "__main__":
    main()
