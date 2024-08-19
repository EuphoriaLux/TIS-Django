from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def duration_in_days(start_date, end_date):
    if start_date and end_date:
        delta = end_date - start_date
        return f"{delta.days} days"
    return "Duration varies"