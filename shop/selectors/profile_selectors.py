from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField

from shop.models import Orders


def get_profile_orders(customer):
    return (
        Orders.objects
        .filter(customer=customer)
        .select_related('status')
        .prefetch_related('orderitem_set__product')
        .annotate(
            total_items=Sum('orderitem__quantity'),
            unique_items=Count('orderitem__product', distinct=True),
            total_price=ExpressionWrapper(
                Sum(F('orderitem__quantity') * F('orderitem__unit_price')),
                output_field=DecimalField()
            )
        )
        .order_by('-created_date')
    )


def get_empty_orders():
    return Orders.objects.none()
