from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
import os
import logging

logger = logging.getLogger('azure.storage')

class Command(BaseCommand):
    help = 'Sync local media files to Azure Storage'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        count = 0
        errors = 0

        for root, dirs, files in os.walk(media_root):
            for filename in files:
                local_path = os.path.join(root, filename)
                rel_path = os.path.relpath(local_path, media_root)
                
                try:
                    with open(local_path, 'rb') as f:
                        logger.info(f"Uploading {rel_path}")
                        default_storage.save(rel_path, f)
                        count += 1
                        self.stdout.write(f"Uploaded: {rel_path}")
                except Exception as e:
                    errors += 1
                    logger.error(f"Failed to upload {rel_path}: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully uploaded {count} files with {errors} errors'
            )
        )