import os
from .settings import *  # noqa
from .settings import BASE_DIR
# Add at the top of production.py
import logging

# Configure the domain name using the environment variable
CUSTOM_DOMAINS = os.environ.get('CUSTOM_DOMAINS', '').split(',')
ALLOWED_HOSTS = ['.azurewebsites.net', 'localhost', '127.0.0.1', '169.254.130.4']
if 'WEBSITE_HOSTNAME' in os.environ:
    ALLOWED_HOSTS.append(os.environ['WEBSITE_HOSTNAME'])
ALLOWED_HOSTS += [domain.strip() for domain in CUSTOM_DOMAINS if domain.strip()]

# Security settings
CSRF_TRUSTED_ORIGINS = ['https://*.azurewebsites.net']
if 'WEBSITE_HOSTNAME' in os.environ:
    CSRF_TRUSTED_ORIGINS.append(f'https://{os.environ["WEBSITE_HOSTNAME"]}')
CSRF_TRUSTED_ORIGINS += [f'https://{domain.strip()}' for domain in CUSTOM_DOMAINS if domain.strip()]

DEBUG = False

logger = logging.getLogger(__name__)

# Add after your storage configuration
STATICFILES_UPLOAD_LOGGER = logging.getLogger('staticfiles.upload')
STATICFILES_UPLOAD_LOGGER.setLevel(logging.INFO)

# Configure logging handler if needed
if not STATICFILES_UPLOAD_LOGGER.handlers:
    
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    STATICFILES_UPLOAD_LOGGER.addHandler(handler)

# Add to your production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'azure.storage': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# WhiteNoise configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Azure Storage Settings
AZURE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'
AZURE_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER', 'static')
AZURE_MEDIA_CONTAINER = os.getenv('AZURE_MEDIA_CONTAINER', 'media')

# Storage configuration
if AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY:
    # Static files
    STATICFILES_STORAGE = 'azureproject.custom_storage.StaticStorage'
    STATIC_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/"

    # Media files
    DEFAULT_FILE_STORAGE = 'azureproject.custom_storage.MediaStorage'
    MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_MEDIA_CONTAINER}/"
else:
    # Local storage fallback
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Required for Azure Storage
AZURE_OVERWRITE_FILES = True
AZURE_SSL = True
DEFAULT_FILE_STORAGE = 'azureproject.custom_storage.MediaStorage'
STATICFILES_STORAGE = 'azureproject.custom_storage.StaticStorage'

# Azure Storage Specific settings
AZURE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_BLOB_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB
AZURE_BLOB_MAX_PARALLEL = 1
AZURE_BLOB_SOCKET_TIMEOUT = 3600

# Database configuration
conn_str = os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING', '')
if conn_str:
    conn_str_params = {pair.split('=')[0]: pair.split('=')[1] for pair in conn_str.split(' ')}
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': conn_str_params['dbname'],
            'HOST': conn_str_params['host'],
            'USER': conn_str_params['user'],
            'PASSWORD': conn_str_params['password'],
        }
    }

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# Add storages to INSTALLED_APPS if not already present
if 'storages' not in INSTALLED_APPS:
    INSTALLED_APPS += ['storages']

# Azure Storage-specific settings
AZURE_OVERWRITE_FILES = True
AZURE_SSL = True