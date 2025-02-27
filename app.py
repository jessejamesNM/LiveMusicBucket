import os
import uuid
import logging
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from io import BytesIO

# Configuración de Flask
app = Flask(__name__)  # 🔹 Se define la aplicación Flask para Gunicorn

# Configuración de credenciales de AWS
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'mi-aplicacion-imagenes'
REGION = 'us-east-2'

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear cliente S3
def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )

# Subir imagen de perfil a S3
def upload_profile_image_to_s3(file, user_id):
    """
    Sube una imagen de perfil a S3 en la carpeta 'profile_images/{user_id}/'.
    """
    file_name = f"profile_images/{user_id}/{uuid.uuid4()}_{secure_filename(file.filename)}"
    s3_client = get_s3_client()

    try:
        s3_client.upload_fileobj(file, BUCKET_NAME, file_name)
        logger.info("Imagen de perfil subida exitosamente a S3.")
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

# Guardar URL en Firestore (simulado)
def save_image_url_to_firestore(user_id, image_url):
    """
    Simulación de guardado en Firestore (reemplazar con integración real).
    """
    logger.info(f"Guardando URL de imagen en Firestore para user_id {user_id}: {image_url}")
    # Aquí iría la lógica real para Firestore
    return True

# Ruta para subir imágenes de perfil usando HTTP
@app.route('/upload_profile_image', methods=['POST'])
def upload_profile_image():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400

    file = request.files['file']
    user_id = request.form.get('user_id', 'default_user')

    url = upload_profile_image_to_s3(file, user_id)

    if url:
        save_image_url_to_firestore(user_id, url)
        return jsonify({"url": url}), 200
    else:
        return jsonify({"error": "Error al subir la imagen"}), 500

# Obtener imágenes de perfil desde S3
def get_profile_images_from_s3(user_id):
    """
    Recupera las imágenes de perfil desde S3 para el usuario especificado.
    """
    s3_client = get_s3_client()
    profile_folder = f"profile_images/{user_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=profile_folder)
        if 'Contents' in response:
            image_urls = [
                f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{obj['Key']}"
                for obj in response['Contents']
            ]
            return image_urls
        else:
            return []
    except ClientError as e:
        logger.error(f"Error al recuperar imágenes de perfil: {e}")
        return []

# Ruta para obtener imágenes de perfil desde S3
@app.route('/get_profile_images', methods=['GET'])
def get_profile_images():
    user_id = request.args.get('user_id', 'default_user')

    image_urls = get_profile_images_from_s3(user_id)

    if image_urls:
        return jsonify({"image_urls": image_urls}), 200
    else:
        return jsonify({"error": "No se encontraron imágenes de perfil"}), 404

# Ruta para subir imágenes de trabajo usando HTTP
@app.route('/upload_work_image', methods=['POST'])
def upload_work_image():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400

    file = request.files['file']
    user_id = request.form.get('user_id', 'default_user')

    url = upload_work_image_to_s3(file, user_id)

    if url:
        return jsonify({"url": url}), 200
    else:
        return jsonify({"error": "Error al subir la imagen"}), 500

# Obtener imágenes de trabajos desde S3
def get_work_images_from_s3(user_id):
    """
    Recupera las imágenes de trabajos desde S3 para el usuario especificado.
    """
    s3_client = get_s3_client()
    work_folder = f"works/{user_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=work_folder)
        if 'Contents' in response:
            image_urls = [
                f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{obj['Key']}"
                for obj in response['Contents']
            ]
            return image_urls
        else:
            return []
    except ClientError as e:
        logger.error(f"Error al recuperar imágenes de trabajos: {e}")
        return []

# Ruta para obtener imágenes de trabajo desde S3
@app.route('/get_work_images', methods=['GET'])
def get_work_images():
    user_id = request.args.get('user_id', 'default_user')

    image_urls = get_work_images_from_s3(user_id)

    if image_urls:
        return jsonify({"image_urls": image_urls}), 200
    else:
        return jsonify({"error": "No se encontraron imágenes de trabajo"}), 404

# 🔹 Necesario para ejecutar en Render con Gunicorn
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
