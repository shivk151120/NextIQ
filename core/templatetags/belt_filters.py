from django import template
from core.models import belt_for_correct

register = template.Library()

@register.filter
def belt(points):
    """Return belt name for a given number of points"""
    return belt_for_correct(points)
