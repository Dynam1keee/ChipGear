from django.db.models import Q
from goods.models import Product

def q_search(query):

    result = Product.objects.filter(Q(name__icontains=query))
    print(query)
    print(result)
    return result
