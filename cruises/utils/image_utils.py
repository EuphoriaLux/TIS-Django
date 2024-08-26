import os
from django.conf import settings
from django.contrib.staticfiles import finders

def get_image_path(image_name):
    # First, try to find the image in the static files
    static_path = finders.find(os.path.join('images', image_name))
    if static_path:
        return static_path

    # If not found in static, check STATIC_ROOT
    if settings.STATIC_ROOT:
        static_root_path = os.path.join(settings.STATIC_ROOT, 'images', image_name)
        if os.path.exists(static_root_path):
            return static_root_path

    # If not found in static, check MEDIA_ROOT for brand logos
    if settings.MEDIA_ROOT:
        media_root_path = os.path.join(settings.MEDIA_ROOT, 'brand_logos', image_name)
        if os.path.exists(media_root_path):
            return media_root_path

    # If the file is not found in any of the above locations, return None
    return None