import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )


def upload_file_to_r2(file_content: bytes, file_name: str, content_type: str):
    client = get_r2_client()
    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=file_name,
            Body=file_content,
            ContentType=content_type,
        )
        return (
            f'{settings.R2_ENDPOINT_URL}/{settings.R2_BUCKET_NAME}/{file_name}'
        )
    except ClientError as e:
        print(f'Error uploading file to R2: {str(e)}')
        return None
