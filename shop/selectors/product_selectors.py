from django.db.models import Count

from shop.models import Product, Category


def get_catalog_products(category='', sort=''):
    qs = Product.objects.select_related('category')

    if category:
        qs = qs.filter(category_id=category)

    if sort == 'price_asc':
        qs = qs.order_by('price')
    elif sort == 'price_desc':
        qs = qs.order_by('-price')
    elif sort == 'popularity':
        qs = qs.annotate(order_count=Count('orderitem')).order_by('-order_count')

    return qs


def get_catalog_categories():
    return Category.objects.all()
