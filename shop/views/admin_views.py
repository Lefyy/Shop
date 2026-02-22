from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from ..forms import ProductForm
from ..services.statistics_service import get_statistics
from ..selectors.admin_selectors import (
    get_admin_customers,
    get_admin_orders,
    get_all_order_statuses,
    get_order_or_404,
    get_order_status_or_404,
    get_admin_products,
    get_all_categories,
    get_product_or_404,
)


def is_staff_user(user):
    return user.is_active and user.is_staff

@user_passes_test(is_staff_user)
def admin_tables_main(request):
    return render(request, 'shop/admin_tables.html')

# ---------- customers ----------
@user_passes_test(is_staff_user)
def admin_customers(request):
    q = request.GET.get('q', '')
    customers = get_admin_customers(search_query=q)
    return render(request, 'shop/admin_customers.html', {'customers': customers, 'search_query': q})

# ---------- orders ----------
@user_passes_test(is_staff_user)
def admin_orders(request, customer_id=None):
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-created_date')

    orders_list, customer = get_admin_orders(
        search_query=search_query,
        sort_by=sort_by,
        customer_id=customer_id,
    )

    return render(request, 'shop/admin_orders.html', {
        'orders': orders_list,
        'all_statuses': get_all_order_statuses(),
        'customer_filter': customer,
        'search_query': search_query,
        'current_sort': sort_by,
    })

@user_passes_test(is_staff_user)
@require_POST
def admin_update_order_status(request, order_id):
    order = get_order_or_404(order_id)
    status_id = request.POST.get('status_id')
    if status_id:
        order.status = get_order_status_or_404(status_id)
        order.save()
    return redirect(request.META.get('HTTP_REFERER', 'shop:admin_orders'))

# ---------- products ----------
@user_passes_test(is_staff_user)
def admin_products(request):
    category_id = request.GET.get('category', '')
    sort = request.GET.get('sort', 'name')
    q = request.GET.get('q', '')
    q_by = request.GET.get('q_by', 'name')

    products_list = get_admin_products(
        category_id=category_id,
        sort=sort,
        q=q,
        q_by=q_by,
    )

    paginator = Paginator(products_list, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'shop/admin_products.html', {
        'products': page_obj,
        'all_categories': get_all_categories(),
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
    product = get_product_or_404(product_id)
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