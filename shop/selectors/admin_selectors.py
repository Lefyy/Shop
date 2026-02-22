from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.shortcuts import get_object_or_404

from shop.models import Customer, Orders, OrderStatus, Product, Category


ADMIN_ORDER_VALID_SORTS = ['id', '-id', 'created_date', '-created_date', 'total_price', '-total_price']
ADMIN_PRODUCT_VALID_SORTS = {
    'price': 'price', '-price': '-price', 'id': 'id', '-id': '-id',
    'name': 'name', '-name': '-name', 'quantity': 'quantity', '-quantity': '-quantity',
}


def get_admin_customers(search_query: str = ''):
    customers = Customer.objects.all().order_by('user__username')
    if search_query:
        customers = customers.filter(user__username__icontains=search_query)
    return customers


def get_admin_orders(search_query: str = '', sort_by: str = '-created_date', customer_id=None):
    orders_list = Orders.objects.select_related('customer', 'status').prefetch_related(
        'orderitem_set', 'orderitem_set__product'
    ).all()

    total_price_expr = ExpressionWrapper(
        Sum(F('orderitem__quantity') * F('orderitem__unit_price')), output_field=DecimalField()
    )

    orders_list = orders_list.annotate(
        total_price=total_price_expr,
        total_items=Sum('orderitem__quantity'),
        unique_items=Count('orderitem__product', distinct=True)
    )

    customer = None
    if customer_id:
        customer = get_object_or_404(Customer, pk=customer_id)
        orders_list = orders_list.filter(customer=customer)

    if search_query:
        orders_list = orders_list.filter(customer__user__username__icontains=search_query)

    if sort_by in ADMIN_ORDER_VALID_SORTS:
        orders_list = orders_list.order_by(sort_by)
    else:
        orders_list = orders_list.order_by('-created_date')

    return orders_list, customer


def get_all_order_statuses():
    return OrderStatus.objects.all()


def get_order_or_404(order_id: int):
    return get_object_or_404(Orders, pk=order_id)


def get_order_status_or_404(status_id: int):
    return get_object_or_404(OrderStatus, pk=status_id)


def get_admin_products(category_id='', sort='name', q='', q_by='name'):
    products_list = Product.objects.select_related('category').all()

    if category_id:
        products_list = products_list.filter(category__id=category_id)

    if q:
        if q_by == 'id' and q.isdigit():
            products_list = products_list.filter(id=int(q))
        else:
            products_list = products_list.filter(name__icontains=q)

    return products_list.order_by(ADMIN_PRODUCT_VALID_SORTS.get(sort, 'name'))


def get_all_categories():
    return Category.objects.all()


def get_product_or_404(product_id: int):
    return get_object_or_404(Product, pk=product_id)
