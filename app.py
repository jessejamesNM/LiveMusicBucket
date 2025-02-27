import os
import uuid
import logging
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from flask import Flask, jsonify, request

# Configuración de Flask
app = Flask(__name__)  # 🔹 Se define la aplicación Flask para Gunicorn

# Configuración de credenciales de AWS
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'mi-aplicacion-imagenes'
REGION = 'us-east-2'

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_message_image_to_s3(file_path, user_id):
    """
    Sube una imagen a S3 en la carpeta de mensajes del usuario.
    """
    file_name = f"MessagesImages/{user_id}/{uuid.uuid4()}_{Path(file_path).name}"
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )
    
    try:
        s3_client.upload_file(file_path, BUCKET_NAME, file_name)
        logger.info("Archivo subido exitosamente a S3.")
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

# 🔹 Ruta para subir imágenes usando HTTP
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id', 'default_user')
    
    file_path = f"/tmp/{file.filename}"
    file.save(file_path)
    
    url = upload_message_image_to_s3(file_path, user_id)
    if url:
        return jsonify({"url": url}), 200
    else:
        return jsonify({"error": "Error al subir la imagen"}), 500

# 🔹 Necesario para ejecutar en Render con Gunicorn
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

    except ClientError as e:
        logger.error(f"Error al subir el archivo a S3: {e}")
        return None
