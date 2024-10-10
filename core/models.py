from django.db import models
from django.contrib.auth.models import User
from storages.backends.s3boto3 import S3Boto3Storage


class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', storage=S3Boto3Storage())
    upload_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True) 

    def __str__(self):
        return self.image.name
