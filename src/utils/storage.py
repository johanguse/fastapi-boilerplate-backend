import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from src.common.config import settings

logger = logging.getLogger(__name__)


def get_r2_client():
    """
    Create and return a boto3 client configured for Cloudflare R2
    """
    return boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )


async def upload_file_to_r2(
    file_content: bytes,
    file_name: str,
    content_type: str,
    bucket_name: Optional[str] = None,
) -> Optional[str]:
    """
    Upload a file to Cloudflare R2 storage
    Args:
        file_content: The file content in bytes
        file_name: The name to give the file in storage
        content_type: The MIME type of the file
        bucket_name: Optional bucket name (defaults to settings.R2_BUCKET_NAME)
    Returns:
        The URL of the uploaded file, or None if upload failed
    """
    try:
        client = get_r2_client()
        bucket = bucket_name or settings.R2_BUCKET_NAME

        client.put_object(
            Bucket=bucket,
            Key=file_name,
            Body=file_content,
            ContentType=content_type,
        )

        file_url = f'{settings.R2_ENDPOINT_URL}/{bucket}/{file_name}'
        logger.info(f'Successfully uploaded file to R2: {file_url}')
        return file_url

    except ClientError as e:
        logger.error(f'Error uploading file to R2: {str(e)}')
        return None


async def delete_file_from_r2(
    file_name: str,
    bucket_name: Optional[str] = None,
) -> bool:
    """
    Delete a file from Cloudflare R2 storage
    Args:
        file_name: The name of the file to delete
        bucket_name: Optional bucket name (defaults to settings.R2_BUCKET_NAME)
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        client = get_r2_client()
        bucket = bucket_name or settings.R2_BUCKET_NAME

        client.delete_object(
            Bucket=bucket,
            Key=file_name,
        )

        logger.info(f'Successfully deleted file from R2: {file_name}')
        return True

    except ClientError as e:
        logger.error(f'Error deleting file from R2: {str(e)}')
        return False


async def get_file_url(
    file_name: str,
    bucket_name: Optional[str] = None,
    expiration: int = 3600,
) -> Optional[str]:
    """
    Get a presigned URL for a file in R2 storage
    Args:
        file_name: The name of the file
        bucket_name: Optional bucket name (defaults to settings.R2_BUCKET_NAME)
        expiration: URL expiration time in seconds (default 1 hour)
    Returns:
        Presigned URL for the file, or None if generation failed
    """
    try:
        client = get_r2_client()
        bucket = bucket_name or settings.R2_BUCKET_NAME

        url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': file_name,
            },
            ExpiresIn=expiration,
        )

        return url

    except ClientError as e:
        logger.error(f'Error generating presigned URL: {str(e)}')
        return None
