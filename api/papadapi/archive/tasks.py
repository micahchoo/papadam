from urllib.parse import urlparse
import subprocess
import os

from minio import Minio
from minio.error import S3Error

from huey.contrib.djhuey import db_task
from huey.contrib.djhuey import task
from django.conf import settings

from papadapi.archive.models import MediaStore

def update_media_processing_status(media,status):
    media.media_processing_status = "Processing started"
    media.save()

@db_task()
def delete_media_post_schedule(media_id):
    media = MediaStore.objects.get(id=media_id)
    media.delete()

@task(retries=3, retry_delay=60)
def convert_to_hls(media_id, output_folder):
    try:
        # Get media object 
        m = MediaStore.objects.get(id=media_id)
        update_media_processing_status(m,"Processing started")
        input_video = m.upload.url
        # Get video resolution
        probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', '-i', m.upload.url],
            capture_output=True, text=True
        )
        width, height = map(int, probe.stdout.strip().split('x'))

        # Define bitrates and resolutions
        resolutions = [(640, 360), (842, 480), (1280, 720)]
        bitrates = ['800k', '1400k', '2800k']

        output_folder = os.path.join(output_folder +"/"+ str(m.uuid))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        commands = ['ffmpeg', '-i', input_video]

        for (res_width, res_height), bitrate in zip(resolutions, bitrates):
            # Only add resolutions lower or equal to source video
            if res_width <= width and res_height <= height:
                commands.extend([
                    '-s', f'{res_width}x{res_height}', '-c:v', 'libx264', '-b:v', bitrate,
                    '-hls_time', '10', '-hls_list_size', '0',
                    '-f', 'hls', f'{output_folder}/stream_{bitrate}.m3u8'
                ])

        subprocess.run(commands, check=True)
        update_media_processing_status(m,"Processing completed")
        
        upload_to_storage.schedule((media_id,output_folder),delay=10)
    except Exception as e:
        print(f"Error occurred: {e}")
        update_media_processing_status(m,"Processing error")
        raise

@task(retries=3, retry_delay=60)
def convert_to_hls_audio(media_id, output_folder):
    try:
        # Get media object 
        m = MediaStore.objects.get(id=media_id)
        update_media_processing_status(m,"Processing started")
        input_audio = m.upload.url

        # Determine the bitrate of the input audio
        probe_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=bit_rate', '-of', 'default=noprint_wrappers=1:nokey=1', '-i', input_audio]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        original_bitrate = int(probe_result.stdout.strip())

        # Define potential output bitrates
        potential_bitrates = [64000, 128000, 256000]  # in bits per second

        # Filter bitrates to be less than or equal to the original
        bitrates = [str(bitrate) + 'k' for bitrate in potential_bitrates if bitrate <= original_bitrate]

        if not bitrates:
            raise ValueError("No suitable bitrate found for conversion.")

        output_folder = os.path.join(output_folder +"/"+ str(m.uuid))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for bitrate in bitrates:
            commands = [
                'ffmpeg', '-i', input_audio, '-vn', '-c:a', 'aac', '-b:a', bitrate,
                '-hls_time', '10', '-hls_list_size', '0',
                '-f', 'hls', f'{output_folder}/stream_{bitrate}.m3u8'
            ]
            subprocess.run(commands, check=True)
        update_media_processing_status(m,"Processing started")
        upload_to_storage.schedule((media_id,output_folder),delay=10)
    except Exception as e:
        print(f"Error occurred: {e}")
        update_media_processing_status(m,"Processing error")
        raise

def create_minio_client(endpoint, access_key, secret_key, secure=True):
    """ 
    Utility function to establish the minio client for the background tasks
    """
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

def get_domain_name(url):
    """
    Extracts the domain name from a URL.

    Args:
    url (str): The URL from which the domain name will be extracted.

    Returns:
    str: The domain name.
    """
    domain_name = None
    # Add scheme if missing for urlparse to work correctly
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc

    # Remove www if it exists
    if domain_name.startswith('www.'):
        domain_name = domain_name[4:]

    if settings.AWS_STORAGE_BUCKET_NAME in domain_name:
        return domain_name.strip(f"{settings.AWS_STORAGE_BUCKET_NAME}.")
    else:
        return domain_name

@task(retries=2,retry_delay=60)
def upload_to_storage(media_id,folder_path):
    m = MediaStore.objects.get(id=media_id)
    update_media_processing_status(m,"Stream uploading")
    is_error = False
    minio_client = create_minio_client(
        get_domain_name(settings.AWS_S3_ENDPOINT_URL), 
        settings.AWS_ACCESS_KEY_ID, 
        settings.AWS_SECRET_ACCESS_KEY, 
        False
        )
    target_path = f"stream/{m.uuid}/"
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, folder_path)
            minio_file_path = os.path.join(target_path, relative_path).replace("\\", "/")

            try:
                # Check if file already exists in MinIO
                try:
                    minio_client.stat_object(bucket_name, minio_file_path)
                    print(f"File {minio_file_path} already exists, skipping...")
                    continue
                except S3Error:
                    # File does not exist, proceed with upload
                    pass

                minio_client.fput_object(bucket_name, minio_file_path, local_file_path)
                # TODO: Should effectively go to a log file instead of a print
                print(f"Uploaded {local_file_path} to {minio_file_path}")
                # This file is now successfully upload. Remove this to save space and reduce duplicate push compute
                os.remove(local_file_path)
            except S3Error as e:
                is_error = True
                print(f"Failed to upload {local_file_path}: {e}")
    if not is_error:
        update_media_processing_status(m,"Stream completed")
    else:
        update_media_processing_status(m, "Stream upload error")
    