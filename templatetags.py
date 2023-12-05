from django import template

register = template.Library()

@register.filter
def get_best_datasheet(bestDatasheets, index):
    return bestDatasheets[index] if bestDatasheets and index < len(bestDatasheets) else None