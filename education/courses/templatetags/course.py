from django import template

register = template.Library()

@register.filter
def model_name(obj):
    """
    Apply to templates filter to get model name for an object
    """
    try:
        return obj.__meta.model_name
    except AttributeError:
        return None