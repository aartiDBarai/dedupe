from __future__ import unicode_literals

from django.db import models

# Create your models here.

class UploadFile(models.Model):
	file_name = models.CharField(max_length = 5000)
	file = models.FileField(upload_to = 'input_files')
	
	class Meta:
		db_table = 'files'

	
