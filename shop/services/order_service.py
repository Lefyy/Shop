import logging
from django.db import transaction
from ..models import Orders, OrderItem, Product, OrderStatus

logger = logging.getLogger(__name__)

@transaction.atomic
def create_order(customer, cart, address=None):
    # Обновляем адрес, если он изменился
    if address and customer.address != address:
        customer.address = address
        customer.save(update_fields=['address'])

    status, _ = OrderStatus.objects.get_or_create(name="Создан")

    order = Orders.objects.create(
        customer=customer,
        status=status,
    )

    for pid, qty in cart.items():
        product = Product.objects.select_for_update().get(pk=int(pid))

        if product.quantity is not None and product.quantity < qty:
            raise ValueError(f'В товаре "{product.name}" доступно только {product.quantity} шт., вы запросили {qty} шт.')

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            unit_price=product.price,
        )

        if product.quantity is not None:
            product.quantity -= qty
            product.save(update_fields=["quantity"])

    return order