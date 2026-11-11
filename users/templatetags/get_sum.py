from django import template

register = template.Library()

@register.simple_tag()
def accumulate_price(order_items):
    total_price = 0
    for item in order_items:
        total_price += item.products_price()
    return total_price