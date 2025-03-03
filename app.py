import os
import uuid
import logging
import json
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import io

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de Flask
app = Flask(__name__)  # 🔹 Se define la aplicación Flask para Gunicorn

# Configuración de credenciales de AWS
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'mi-aplicacion-imagenes'
REGION = 'us-east-2'

# Configuración de Firebase con las credenciales almacenadas como variable de entorno
firebase_cred = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
cred = credentials.Certificate(firebase_cred)
firebase_admin.initialize_app(cred)
db = firestore.client()

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

# Subir imagen a S3
def upload_message_image_to_s3(file, user_id):
    # Crear cliente S3
    s3_client = get_s3_client()

    # Nombre del archivo en S3
    file_name = f"MessagesImages/{user_id}/{uuid.uuid4()}_temp_image_message.jpg"
    
    # Crear la solicitud de subida a S3
    try:
        s3_client.upload_fileobj(file, BUCKET_NAME, file_name)
        logger.info("Imagen subida exitosamente a S3.")
        return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_name}"
    except (FileNotFoundError, NoCredentialsError, ClientError) as e:
        logger.error(f"Error al subir archivo: {e}")
        return None

# Ruta para subir imágenes de mensajes
@app.route('/upload_message_image', methods=['POST'])
def upload_message_image():
    # Obtener el archivo de la solicitud
    file = request.files.get('file')
    user_id = request.form.get('user_id', 'default_user')

    # Verificar si se ha proporcionado el archivo
    if not file:
        return jsonify({"error": "No se encontró el archivo"}), 400

    # Subir la imagen a S3
    url = upload_message_image_to_s3(file, user_id)

    if url:
        return jsonify({"url": url}), 200
    else:
        return jsonify({"error": "Error al subir la imagen"}), 500


# Subir imagen de perfil a S3
def upload_profile_image_to_s3(file, user_id):
    file_name = f"profile_images/{user_id}/{uuid.uuid4()}_{secure_filename(file.filename)}"
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(file, BUCKET_NAME, file_name)
        logger.info("Imagen de perfil subida exitosamente a S3.")
        return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_name}"
    except (FileNotFoundError, NoCredentialsError, ClientError) as e:
        logger.error(f"Error al subir archivo: {e}")
        return None

# Guardar URL en Firestore
def save_image_url_to_firestore(user_id, image_url):
    logger.info(f"Guardando URL de imagen en Firestore para user_id {user_id}: {image_url}")
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'profileImageUrl': image_url
    })
    logger.info("URL guardada correctamente en Firestore")
    return True

# Ruta para subir imágenes de perfil
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
    s3_client = get_s3_client()
    profile_folder = f"profile_images/{user_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=profile_folder)
        if 'Contents' in response:
            return [
                f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{obj['Key']}"
                for obj in response['Contents']
            ]
        return []
    except ClientError as e:
        logger.error(f"Error al recuperar imágenes de perfil: {e}")
        return []

# Ruta para obtener imágenes de perfil
@app.route('/get_profile_images', methods=['GET'])
def get_profile_images():
    user_id = request.args.get('user_id', 'default_user')
    image_urls = get_profile_images_from_s3(user_id)

    if image_urls:
        return jsonify({"image_urls": image_urls}), 200
    else:
        return jsonify({"error": "No se encontraron imágenes de perfil"}), 404

# Subir imagen de trabajo a S3
def upload_work_image_to_s3(file, user_id):
    file_name = f"works/{user_id}/{uuid.uuid4()}_{secure_filename(file.filename)}"
    s3_client = get_s3_client()
    try:
        s3_client.upload_fileobj(file, BUCKET_NAME, file_name)
        logger.info("Imagen de trabajo subida exitosamente a S3.")
        return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_name}"
    except (FileNotFoundError, NoCredentialsError, ClientError) as e:
        logger.error(f"Error al subir archivo: {e}")
        return None

# Ruta para subir imágenes de trabajo
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
    s3_client = get_s3_client()
    work_folder = f"works/{user_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=work_folder)
        if 'Contents' in response:
            return [
                f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{obj['Key']}"
                for obj in response['Contents']
            ]
        return []
    except ClientError as e:
        logger.error(f"Error al recuperar imágenes de trabajos: {e}")
        return []

# Ruta para obtener imágenes de trabajo
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
    port = int(os.environ.get("PORT", 10000))  # Usa el puerto de Render o 10000 por defecto
    app.run(host='0.0.0.0', port=port)

