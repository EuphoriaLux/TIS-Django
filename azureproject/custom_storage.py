from storages.backends.azure_storage import AzureStorage
import os

class StaticStorage(AzureStorage):
    account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    azure_container = 'static'
    expiration_secs = None
    overwrite_files = True

class MediaStorage(AzureStorage):
    account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    azure_container = 'media'
    expiration_secs = None