from django.shortcuts import get_object_or_404

from shop.models import Orders


def get_order_for_user(order_id: int, customer):
    """
    Возвращает заказ пользователя.
    Используется на странице успешного заказа.
    """

    return get_object_or_404(
        Orders.objects.select_related("customer", "status"),
        pk=order_id,
        customer=customer,
    )
