from storages.backends.azure_storage import AzureStorage
import os
import hashlib
import logging

logger = logging.getLogger('azure.storage')

class OptimizedAzureStorageMixin:
    def _get_content_md5(self, content):
        """Calculate MD5 hash of content"""
        if hasattr(content, 'read'):
            md5 = hashlib.md5()
            chunk = content.read(4096)
            while chunk:
                md5.update(chunk)
                chunk = content.read(4096)
            content.seek(0)  # Reset file pointer
            return md5.hexdigest()
        return None

    def _save(self, name, content):
        """Implement optimized save with conditional upload"""
        logger.info(f"Processing file: {name}")
        
        # Calculate content hash
        content_md5 = self._get_content_md5(content)
        
        if content_md5:
            try:
                # Check if blob exists and compare hashes
                blob_client = self.client.get_blob_client(
                    container=self.azure_container,
                    blob=name
                )
                
                try:
                    props = blob_client.get_blob_properties()
                    existing_md5 = props.content_settings.content_md5
                    
                    if existing_md5 and existing_md5.decode('utf-8') == content_md5:
                        logger.info(f"File {name} unchanged, skipping upload")
                        return name
                    
                except Exception as e:
                    logger.debug(f"Error checking blob {name}: {str(e)}")
            
            except Exception as e:
                logger.debug(f"Blob {name} does not exist: {str(e)}")
        
        logger.info(f"Uploading file: {name}")
        return super()._save(name, content)

class StaticStorage(OptimizedAzureStorageMixin, AzureStorage):
    account_name = 'devqgemc2diauefestorage'
    azure_container = 'static'
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    
    def get_content_type(self):
        """Set proper content types for different file extensions"""
        name = getattr(self, 'name', None)
        if name is None:
            return 'application/octet-stream'
            
        content_types = {
            '.woff2': 'font/woff2',
            '.woff': 'font/woff',
            '.ttf': 'font/ttf',
            '.eot': 'application/vnd.ms-fontobject',
            '.svg': 'image/svg+xml',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.map': 'application/json',
            '.ico': 'image/x-icon'
        }
        
        for ext, content_type in content_types.items():
            if name.endswith(ext):
                return content_type
        
        return super().get_content_type()

    def get_object_parameters(self, name):
        """Set cache control and other parameters"""
        params = super().get_object_parameters(name)
        
        # Define caching strategies
        caching_rules = {
            'long_term': {
                'extensions': ['.woff2', '.woff', '.ttf', '.eot', '.svg'], 
                'duration': 31536000  # 1 year
            },
            'medium_term': {
                'extensions': ['.css', '.js', '.map'], 
                'duration': 604800    # 1 week
            },
            'short_term': {
                'extensions': ['.ico'], 
                'duration': 86400     # 1 day
            }
        }

        # Apply caching rules
        for rule in caching_rules.values():
            if any(name.endswith(ext) for ext in rule['extensions']):
                params['CacheControl'] = f'public, max-age={rule["duration"]}'
                break
        else:
            params['CacheControl'] = 'public, max-age=3600'  # 1 hour default

        params['ContentType'] = self.get_content_type()
        return params

class MediaStorage(OptimizedAzureStorageMixin, AzureStorage):
    account_name = 'devqgemc2diauefestorage'
    azure_container = 'media'
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        params['CacheControl'] = 'public, max-age=3600'  # 1 hour for media files
        return params