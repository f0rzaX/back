from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import Image
import boto3
import os
from botocore.config import Config
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]


from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "password", "password2", "email")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Oops! This username is already taken. Please choose another one."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Oops! An account with this email already exists."
            )
        return value

    def validate(self, data):
        """
        Check that the two password entries match.
        """
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data["username"], email=validated_data["email"]
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class ImageSerializer(serializers.ModelSerializer):
    signed_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["id", "image", "upload_date", "description", "signed_url"]
        read_only_fields = ["upload_date", "description"]

    def get_signed_url(self, obj):
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_S3_REGION_NAME"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
            ),
        )

        # Generate a presigned URL for retrieving the object
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": os.getenv("AWS_STORAGE_BUCKET_NAME"),
                    "Key": str(obj.image),
                },
                ExpiresIn=3600,  # URL expires in 1 hour
            )
            return url
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            return None
