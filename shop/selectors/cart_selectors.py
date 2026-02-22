from django.shortcuts import get_object_or_404

from shop.models import Product


def get_product_by_id_or_404(product_id: int):
    return get_object_or_404(Product, pk=product_id)


def get_product_by_id(product_id: int):
    return Product.objects.get(id=product_id)
