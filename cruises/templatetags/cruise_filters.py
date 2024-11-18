# cruises/templatetags/cruise_filters.py

from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def duration_in_days(start_date, end_date):
    if start_date and end_date:
        delta = end_date - start_date
        return f"{delta.days + 1} days"
    return "Duration varies"

@register.filter
def star_range(value):
    """Convert integer to range for star rating"""
    return range(int(value))

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    return dictionary.get(key)

@register.simple_tag
def get_price_display(min_price):
    """Format price display"""
    if min_price:
        return f"From €{min_price:,.2f}"
    return "Price on request"