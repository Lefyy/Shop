from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum, F, Q, ExpressionWrapper, DecimalField
from django.db.models import Value as V
from django.db import transaction
from decimal import Decimal
from datetime import timedelta
from .forms import CheckoutForm, CustomUserCreationForm, ProductForm 
from .models import Product, Category, Orders, OrderItem, OrderStatus, Customer, AuthUser

# ---------- Helpers for session cart ----------
CART_SESSION_ID = 'cart'

def _get_cart(request):
    return request.session.setdefault(CART_SESSION_ID, {})

def _save_cart(request, cart):
    request.session[CART_SESSION_ID] = cart
    request.session.modified = True

# ---------- Product list / filter / sort ----------
class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.all()
        cat = self.request.GET.get('category')
        if cat:
            qs = qs.filter(category__id=cat)
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            qs = qs.order_by('price')
        elif sort == 'price_desc':
            qs = qs.order_by('-price')
        elif sort == 'popularity':
            qs = qs.annotate(order_count=Count('orderitem')).order_by('-order_count')
        return qs.select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_sort'] = self.request.GET.get('sort', '')
        return ctx

# ---------- Product detail ----------
class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'

# -------------- Profile --------------

@login_required
def profile(request):
    user = request.user
    customer = getattr(user, 'customer', None)
    # Получаем заказы текущего покупателя
    orders = Orders.objects.filter(customer=customer).select_related('status').prefetch_related('orderitem_set__product').annotate(
        total_items=Sum('orderitem__quantity'),
        unique_items=Count('orderitem__product', distinct=True),
        total_price=ExpressionWrapper(Sum(F('orderitem__quantity') * F('orderitem__unit_price')), output_field=DecimalField())
    ).order_by('-created_date')

    # профильный POST для изменения телефона/адреса
    if request.method == 'POST' and 'save_profile' in request.POST:
        phone = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        if customer:
            customer.phone_number = phone
            customer.address = address
            customer.save()
        return redirect('shop:profile')

    if 'change_password' in request.POST:
        pwd_form = PasswordChangeForm(user=user, data=request.POST)
    else:
        pwd_form = PasswordChangeForm(user=user)

    try:
        fld = pwd_form.fields
        if 'old_password' in fld:
            fld['old_password'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Введите текущий пароль'
            })
        if 'new_password1' in fld:
            fld['new_password1'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Введите новый пароль'
            })
        if 'new_password2' in fld:
            fld['new_password2'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Повторите новый пароль'
            })
    except Exception:
        pass

    pwd_message = None
    if request.method == 'POST' and 'change_password' in request.POST:
        if pwd_form.is_valid():
            pwd_form.save()
            update_session_auth_hash(request, pwd_form.user)
            pwd_message = 'Пароль успешно изменён.'
        else:
            pwd_message = 'Ошибка при изменении пароля.'

    context = {
        'orders': orders,
        'customer': customer,
        'pwd_form': pwd_form,
        'pwd_message': pwd_message,
    }
    return render(request, 'shop/profile.html', context)

# ---------- Cart operations ----------

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = _get_cart(request)
    pid = str(product_id)
    qty = int(request.POST.get('quantity', 1))
    if product.quantity is not None and qty > product.quantity:
        qty = product.quantity
    if pid in cart:
        new_qty = cart[pid]['quantity'] + qty
        if product.quantity is not None and new_qty > product.quantity:
            cart[pid]['quantity'] = product.quantity
        else:
            cart[pid]['quantity'] = new_qty
    else:
        cart[pid] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': qty,
        }
    _save_cart(request, cart)
    return redirect('shop:view_cart')

def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        _save_cart(request, cart)
    return redirect('shop:view_cart')

def view_cart(request):
    cart = _get_cart(request)
    items = []
    total = Decimal('0.00')

    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=product_ids)
    product_dict = {p.id: p for p in products}

    for pid, data in cart.items():
        price = Decimal(data['price'])
        qty = int(data['quantity'])
        subtotal = price * qty
        total += subtotal
        items.append({
            'product_id': int(pid),
            'name': data['name'],
            'price': price,
            'quantity': qty,
            'subtotal': subtotal,
        })

    # render template with product_dict
    return render(request, 'shop/cart.html', {'items': items, 'total': total, 'product_dict': product_dict})

@require_POST
def update_cart(request):
    cart = _get_cart(request)
    if not cart:
        messages.info(request, "Корзина пуста.")
        return redirect('shop:view_cart')

    # Получаем все product_ids, которые присутствуют в POST в виде quantity_<id>
    updates = {}
    for key, value in request.POST.items():
        if not key.startswith('quantity_'):
            continue
        try:
            pid = int(key.split('_', 1)[1])
        except ValueError:
            continue
        try:
            qty = int(value)
        except (TypeError, ValueError):
            messages.error(request, f"Неверное количество для товара {pid}.")
            continue
        updates[pid] = qty

    # Загрузим продукты одной выборкой
    product_ids = list(updates.keys())
    products = Product.objects.filter(id__in=product_ids)
    prod_map = {p.id: p for p in products}

    # Пройдём по обновлениям и применим изменения с валидацией
    any_changes = False
    for pid, new_qty in updates.items():
        pid_str = str(pid)
        if pid_str not in cart:
            # возможно товар был удалён ранее — игнорируем
            continue

        product = prod_map.get(pid)
        if product is None:
            # товар удалён из базы — убираем из корзины
            del cart[pid_str]
            any_changes = True
            messages.warning(request, f"Товар с id {pid} больше недоступен и был удалён из корзины.")
            continue

        # нормализуем new_qty: если <=0 — удаляем
        if new_qty <= 0:
            del cart[pid_str]
            any_changes = True
            continue

        # проверка на максимальное доступное количество
        if product.quantity is not None and new_qty > product.quantity:
            cart[pid_str]['quantity'] = product.quantity
            any_changes = True
            messages.warning(request,
                f'Количество для "{product.name}" было уменьшено до доступного ({product.quantity}).')
        else:
            # применяем новое значение
            if cart[pid_str]['quantity'] != new_qty:
                cart[pid_str]['quantity'] = new_qty
                any_changes = True

    if any_changes:
        _save_cart(request, cart)
        messages.success(request, "Корзина обновлена.")
    else:
        messages.info(request, "Изменений не обнаружено.")

    return redirect('shop:view_cart')

# ---------- Checkout ----------
@login_required
@transaction.atomic
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        return redirect('shop:product_list')

    # подготовка items и total для восстановления контента при ошибке
    def build_cart_items_and_total(cart):
        items = []
        total = Decimal('0.00')
        for pid, data in cart.items():
            price = Decimal(data['price'])
            qty = int(data['quantity'])
            subtotal = price * qty
            total += subtotal
            items.append({
                'product_id': int(pid),
                'name': data['name'],
                'price': price,
                'quantity': qty,
                'subtotal': subtotal,
            })
        return items, total

    # GET — показать форму с автозаполнением адреса
    if request.method == 'GET':
        customer = getattr(request.user, 'customer', None)
        initial = {}
        if customer and customer.address:
            initial['address'] = customer.address
        form = CheckoutForm(initial=initial)
        items, total = build_cart_items_and_total(cart)
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    # POST — обработка оформления
    form = CheckoutForm(request.POST)
    items, total = build_cart_items_and_total(cart)
    if not form.is_valid():
        # сразу вернуть с ошибками
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    # основная логика: проверка остатков и создание заказа в транзакции
    customer = getattr(request.user, 'customer', None)
    if customer is None:
        form.add_error(None, 'Профиль покупателя не найден. Пожалуйста, свяжитесь с администратором.')
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    status, _ = OrderStatus.objects.get_or_create(name='Создан')
    try:
        # Создаём заказ (можно сразу указать адрес при наличии поля Orders.address, если он есть)
        order = Orders.objects.create(customer=customer, status=status)
        total_calc = Decimal('0.00')

        # Для каждого продукта — блокировка записи и проверка количества
        for pid, data in cart.items():
            product = Product.objects.select_for_update().get(pk=int(pid))
            qty = int(data['quantity'])
            if product.quantity is not None and qty > product.quantity:
                # Откатываем транзакцию и возвращаем ошибку в форме
                raise ValueError(f'В товаре "{product.name}" доступно только {product.quantity} шт., вы запросили {qty} шт.')

            unit_price = Decimal(data['price'])
            OrderItem.objects.create(order=order, product=product, quantity=qty, unit_price=unit_price)

            # уменьшим склад
            if product.quantity is not None:
                product.quantity = product.quantity - qty
                if product.quantity < 0:
                    product.quantity = 0
                product.save()

            total_calc += unit_price * qty

        # Сохраняем адрес пользователя (если он ввёл новый)
        address = form.cleaned_data.get('address', '').strip()
        if address:
            if customer.address != address:
                customer.address = address
                customer.save()

        # очищаем корзину и редирект на страницу успеха
        request.session.pop(CART_SESSION_ID, None)
        return redirect('shop:order_success', order_id=order.pk)

    except Product.DoesNotExist:
        form.add_error(None, 'Один из товаров в корзине больше недоступен.')
        # откат транзакции автоматически
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    except ValueError as ve:
        form.add_error(None, str(ve))
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    except Exception as e:
        form.add_error(None, 'Ошибка оформления заказа. Попробуйте позже.')
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Orders, pk=order_id)
    return render(request, 'shop/order_success.html', {'order': order})

# ---------- Admin tables view ----------
def is_staff_user(u):
    return u.is_active and u.is_staff

# 1. Главная страница админки (бывшая admin_tables)
@user_passes_test(is_staff_user)
def admin_tables_main(request):
    """
    Отображает главную страницу админки с тремя кнопками.
    """
    # Теперь эта функция просто рендерит шаблон с кнопками
    return render(request, 'shop/admin_tables.html')


# 2. Страница "Покупатели"
@user_passes_test(is_staff_user)
def admin_customers(request):
    """
    Отображает список покупателей (Customer) с поиском по логину.
    """
    search_query = request.GET.get('q', '')
    
    customers_list = Customer.objects.all().order_by('login')
    
    if search_query:
        customers_list = customers_list.filter(login__icontains=search_query)
        
    context = {
        'customers': customers_list,
        'search_query': search_query,
    }
    return render(request, 'shop/admin_customers.html', context)


# 3. Страница "Заказы" (общая и для покупателя)
@user_passes_test(is_staff_user)
def admin_orders(request, customer_id=None):
    """
    Отображает список заказов.
    Может быть отфильтрован по customer_id.
    Поддерживает поиск по логину покупателя и сортировку.
    """
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-created_date') # Сортировка по умолчанию

    orders_list = Orders.objects.select_related('customer', 'status').prefetch_related(
        'orderitem_set', 
        'orderitem_set__product'
    ).all()

    # --- Агрегация ---
    # Мы используем ExpressionWrapper для корректного подсчета total_price
    total_price_expr = ExpressionWrapper(
        Sum(F('orderitem__quantity') * F('orderitem__unit_price')),
        output_field=DecimalField()
    )
    
    orders_list = orders_list.annotate(
        total_price=total_price_expr,
        total_items=Sum('orderitem__quantity'),
        unique_items=Count('orderitem__product', distinct=True)
    )

    # --- Фильтрация ---
    customer = None
    if customer_id:
        customer = get_object_or_404(Customer, pk=customer_id)
        orders_list = orders_list.filter(customer=customer)
        
    if search_query:
        orders_list = orders_list.filter(customer__login__icontains=search_query)

    # --- Сортировка ---
    valid_sorts = ['id', '-id', 'created_date', '-created_date', 'total_price', '-total_price']
    if sort_by in valid_sorts:
        orders_list = orders_list.order_by(sort_by)
    else:
        orders_list = orders_list.order_by('-created_date') # По умолчанию

    # Получаем все статусы для выпадающего списка
    all_statuses = OrderStatus.objects.all()

    context = {
        'orders': orders_list,
        'all_statuses': all_statuses,
        'customer_filter': customer,
        'search_query': search_query,
        'current_sort': sort_by,
    }
    return render(request, 'shop/admin_orders.html', context)


# 4. Обновление статуса заказа (для формы в таблице)
@user_passes_test(is_staff_user)
@require_POST # Принимаем только POST запросы
def admin_update_order_status(request, order_id):
    """
    Обновляет статус заказа.
    """
    order = get_object_or_404(Orders, pk=order_id)
    status_id = request.POST.get('status_id')
    
    if status_id:
        new_status = get_object_or_404(OrderStatus, pk=status_id)
        order.status = new_status
        order.save()
        
    # Возвращаемся на ту же страницу, с которой пришли
    return redirect(request.META.get('HTTP_REFERER', 'shop:admin_orders'))


# 5. Страница "Продукты"
@user_passes_test(is_staff_user)
def admin_products(request):
    """
    Отображает список продуктов с фильтром по категории и пагинацией.
    """
    category_id = request.GET.get('category', '')
    sort = request.GET.get('sort', 'name')  # по умолчанию name
    q = request.GET.get('q', '')
    q_by = request.GET.get('q_by', 'name')  # 'id' или 'name'

    products_list = Product.objects.select_related('category').all()

    if category_id:
        products_list = products_list.filter(category__id=category_id)

    if q:
        if q_by == 'id' and q.isdigit():
            products_list = products_list.filter(id=int(q))
        else:
            products_list = products_list.filter(name__icontains=q)

    # сортировка
    valid_sorts = {
        'price': 'price',
        '-price': '-price',
        'id': 'id',
        '-id': '-id',
        'name': 'name',
        '-name': '-name',
        'quantity': 'quantity',
        '-quantity': '-quantity',
    }
    sort_field = valid_sorts.get(sort, 'name')
    products_list = products_list.order_by(sort_field)

    all_categories = Category.objects.all()

    paginator = Paginator(products_list, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'all_categories': all_categories,
        'current_category': category_id,
        'current_sort': sort,
        'search_query': q,
        'search_by': q_by,
    }
    return render(request, 'shop/admin_products.html', context)


# 6. Добавление продукта
@user_passes_test(is_staff_user)
def admin_add_product(request):
    """
    Форма для добавления нового продукта.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('shop:admin_products')
    else:
        form = ProductForm()
        
    context = {
        'form': form,
        'form_title': 'Добавить новый товар'
    }
    return render(request, 'shop/admin_product_form.html', context)


# 7. Редактирование продукта
@user_passes_test(is_staff_user)
def admin_edit_product(request, product_id):
    """
    Форма для редактирования существующего продукта.
    """
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('shop:admin_products')
    else:
        form = ProductForm(instance=product)
        
    context = {
        'form': form,
        'form_title': f'Редактировать: {product.name}'
    }
    return render(request, 'shop/admin_product_form.html', context)

@user_passes_test(is_staff_user)
def admin_statistics(request):
    """
    Админская страница со статистикой и топ-10 списками.
    GET параметр: period in ('all', 'day', 'month', 'year') — по умолчанию 'all'.
    """
    period = request.GET.get('period', 'all')
    now = timezone.now()

    # Опционально: сделать начало периода более «чистым»
    if period == 'day':
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'month':
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'year':
        period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        period_start = None  # all time

    order_date_filter = {}
    if period_start:
        order_date_filter['order__created_date__gte'] = period_start

    from .models import OrderItem, Product, Category, Customer

    # выражение для line total
    line_total_expr = ExpressionWrapper(
        F('quantity') * F('unit_price'),
        output_field=DecimalField(max_digits=18, decimal_places=2)
    )

    # 1) Топ продуктов по количеству (и самый популярный — first)
    prod_qty_qs = (
        OrderItem.objects.filter(**order_date_filter)
        .values('product__id', 'product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )
    top_product = prod_qty_qs.first()
    top_products = list(prod_qty_qs[:10])

    # Топ продуктов по выручке (для блока выручки — ТОП-10 товаров по line_total)
    prod_rev_qs = (
        OrderItem.objects.filter(**order_date_filter)
        .values('product__id', 'product__name')
        .annotate(total_revenue=Sum(line_total_expr))
        .order_by('-total_revenue')
    )
    top_products_revenue = list(prod_rev_qs[:10])

    # 2) Общая выручка за период
    revenue_agg = OrderItem.objects.filter(**order_date_filter).aggregate(
        total_revenue=Sum(line_total_expr)
    )
    total_revenue = revenue_agg.get('total_revenue') or 0

    # 3) Топ категорий по количеству
    cat_qs = (
        OrderItem.objects.filter(**order_date_filter)
        .values('product__category__id', 'product__category__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )
    top_category = cat_qs.first()
    top_categories = list(cat_qs[:10])

    # 4) Топ покупателей по сумме покупок (total_spent)
    cust_qs = (
        OrderItem.objects.filter(**order_date_filter)
        .values('order__customer__id', 'order__customer__login')
        .annotate(total_spent=Sum(line_total_expr))
        .order_by('-total_spent')
    )
    top_customer = cust_qs.first()
    top_customers = list(cust_qs[:10])

    context = {
        'period': period,
        'period_choices': [('all', 'За всё время'), ('day', 'За день'), ('month', 'За месяц'), ('year', 'За год')],
        'top_product': top_product,
        'top_products': top_products,
        'top_products_revenue': top_products_revenue,
        'total_revenue': total_revenue,
        'top_category': top_category,
        'top_categories': top_categories,
        'top_customer': top_customer,
        'top_customers': top_customers,
    }
    return render(request, 'shop/admin_statistics.html', context)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})