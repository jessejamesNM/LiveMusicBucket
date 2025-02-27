
# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_message_image_to_s3(file_path, user_id):
    """
    Sube una imagen a S3 en la carpeta de mensajes del usuario.
    
    :param file_path: Ruta local del archivo a subir.
    :param user_id: ID del usuario para organizar las imágenes en S3.
    :return: URL del archivo subido o None si falla.
    """
    # Generar un nombre único para la imagen en la carpeta de mensajes
    file_name = f"MessagesImages/{user_id}/{uuid.uuid4()}_{Path(file_path).name}"

    # Crear cliente de S3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )

    try:
        # Subir el archivo a S3
        s3_client.upload_file(file_path, BUCKET_NAME, file_name)
        logger.info("Archivo subido exitosamente a S3.")

        # Generar la URL del archivo subido
        file_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_name}"
        return file_url
    except FileNotFoundError:
        logger.error("El archivo no fue encontrado.")
        return None
    except NoCredentialsError:
        logger.error("Credenciales de AWS no disponibles.")
        return None
    except ClientError as e:
        logger.error(f"Error al subir el archivo a S3: {e}")
        return None

# Ejemplo de uso
if __name__ == "__main__":
    file_path = "ruta/al/archivo/imagen.jpg"  # Reemplaza con la ruta de tu archivo
    user_id = "12345"  # Reemplaza con el ID del usuario
    url = upload_message_image_to_s3(file_path, user_id)
    if url:
        print(f"URL del archivo subido: {url}")
    else:
        print("Error al subir el archivo.")
