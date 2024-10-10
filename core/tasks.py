import openai
from celery import shared_task
from .models import Image
from .serializers import ImageSerializer
import time
import boto3
from botocore.config import Config
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@shared_task
def process_image(image_id):
    # Fetch the image from the database
    image = Image.objects.get(id=image_id)

    # Generate a presigned URL to send to the OpenAI API
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_S3_REGION_NAME"),
        config=Config(signature_version="s3v4"),
    )

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": os.getenv("AWS_STORAGE_BUCKET_NAME"),
            "Key": str(image.image),
        },
        ExpiresIn=1800,  # URL expires in 30 minutes
    )

    print(f"Presigned URL: {presigned_url}")

    # OpenAI API call
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_ID"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's in this image? Go through the image, look for background setting, objects and people and describe it within 70 words.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": presigned_url},
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        # Get the description from the API response
        description = response.choices[0].message.content

        image.description = description
        image.save()

        return f"Processed image with ID {image_id} and generated description."

    except Exception as e:
        print(f"Error processing image with OpenAI API: {e}")
        return None
