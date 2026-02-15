from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField

from ..models import Customer, Orders, OrderStatus, Product, Category
from ..forms import ProductForm
from ..services.statistics_service import get_statistics

def is_staff_user(user):
    return user.is_active and user.is_staff

@user_passes_test(is_staff_user)
def admin_tables_main(request):
    return render(request, 'shop/admin_tables.html')

# ---------- customers ----------
@user_passes_test(is_staff_user)
def admin_customers(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.all().order_by('user__username')
    if q:
        customers = customers.filter(user__username__icontains=q)
    return render(request, 'shop/admin_customers.html', {'customers': customers, 'search_query': q})

# ---------- orders ----------
@user_passes_test(is_staff_user)
def admin_orders(request, customer_id=None):
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-created_date')

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

    valid_sorts = ['id', '-id', 'created_date', '-created_date', 'total_price', '-total_price']
    if sort_by in valid_sorts:
        orders_list = orders_list.order_by(sort_by)
    else:
        orders_list = orders_list.order_by('-created_date')

    return render(request, 'shop/admin_orders.html', {
        'orders': orders_list,
        'all_statuses': OrderStatus.objects.all(),
        'customer_filter': customer,
        'search_query': search_query,
        'current_sort': sort_by,
    })

@user_passes_test(is_staff_user)
@require_POST
def admin_update_order_status(request, order_id):
    order = get_object_or_404(Orders, pk=order_id)
    status_id = request.POST.get('status_id')
    if status_id:
        order.status = get_object_or_404(OrderStatus, pk=status_id)
        order.save()
    return redirect(request.META.get('HTTP_REFERER', 'shop:admin_orders'))

# ---------- products ----------
@user_passes_test(is_staff_user)
def admin_products(request):
    category_id = request.GET.get('category', '')
    sort = request.GET.get('sort', 'name')
    q = request.GET.get('q', '')
    q_by = request.GET.get('q_by', 'name')

    products_list = Product.objects.select_related('category').all()

    if category_id:
        products_list = products_list.filter(category__id=category_id)

    if q:
        if q_by == 'id' and q.isdigit():
            products_list = products_list.filter(id=int(q))
        else:
            products_list = products_list.filter(name__icontains=q)

    valid_sorts = {
        'price': 'price', '-price': '-price', 'id': 'id', '-id': '-id',
        'name': 'name', '-name': '-name', 'quantity': 'quantity', '-quantity': '-quantity',
    }
    products_list = products_list.order_by(valid_sorts.get(sort, 'name'))

    paginator = Paginator(products_list, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'shop/admin_products.html', {
        'products': page_obj,
        'all_categories': Category.objects.all(),
        'current_category': category_id,
        'current_sort': sort,
        'search_query': q,
        'search_by': q_by,
    })

@user_passes_test(is_staff_user)
def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('shop:admin_products')
    else:
        form = ProductForm()
        
    return render(request, 'shop/admin_product_form.html', {'form': form, 'form_title': 'Добавить новый товар'})

@user_passes_test(is_staff_user)
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('shop:admin_products')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'shop/admin_product_form.html', {'form': form, 'form_title': f'Редактировать: {product.name}'})

# ---------- statistics ----------
@user_passes_test(is_staff_user)
def admin_statistics(request):
    period = request.GET.get('period', 'all')
    stats = get_statistics(period)
    
    context = {
        "period": period,
        "period_choices": [('all', 'За всё время'), ('day', 'За день'), ('month', 'За месяц'), ('year', 'За год')],
        **stats
    }
    return render(request, 'shop/admin_statistics.html', context)