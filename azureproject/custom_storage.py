from storages.backends.azure_storage import AzureStorage
import os

class StaticStorage(AzureStorage):
    account_name = 'devqgemc2diauefestorage'
    azure_container = 'static'
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')  # Get key from environment variable

    def get_content_type(self):
        """
        Set proper content types for different file extensions
        """
        name = getattr(self, 'name', None)
        if name is None:
            return 'application/octet-stream'
            
        # Map file extensions to MIME types
        if name.endswith('.woff2'):
            return 'font/woff2'
        elif name.endswith('.woff'):
            return 'font/woff'
        elif name.endswith('.ttf'):
            return 'font/ttf'
        elif name.endswith('.eot'):
            return 'application/vnd.ms-fontobject'
        elif name.endswith('.svg'):
            return 'image/svg+xml'
        elif name.endswith('.css'):
            return 'text/css'
        elif name.endswith('.js'):
            return 'application/javascript'
        
        return super().get_content_type()

    def get_object_parameters(self, name):
        """
        Set cache control and other parameters for uploaded files
        """
        params = super().get_object_parameters(name)
        
        # Set cache control based on file type
        if any(name.endswith(ext) for ext in ['.woff2', '.woff', '.ttf', '.eot', '.svg']):
            params['CacheControl'] = 'public, max-age=31536000'  # Cache fonts for 1 year
        elif any(name.endswith(ext) for ext in ['.css', '.js']):
            params['CacheControl'] = 'public, max-age=86400'  # Cache CSS/JS for 1 day
        else:
            params['CacheControl'] = 'public, max-age=3600'  # Cache other files for 1 hour
        
        # Set CORS-related headers
        params['ContentType'] = self.get_content_type()
        
        return params

class MediaStorage(AzureStorage):
    account_name = 'devqgemc2diauefestorage'
    azure_container = 'media'
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')  # Get key from environment variable

    def get_object_parameters(self, name):
        """
        Set cache control and other parameters for uploaded files
        """
        params = super().get_object_parameters(name)
        params['CacheControl'] = 'public, max-age=3600'  # Cache media files for 1 hour
        return params