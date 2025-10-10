from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.db.models import Count
from django.db import transaction
from decimal import Decimal
from .models import Product, Category, Orders, OrderItem, OrderStatus, Customer, AuthUser
from .forms import CheckoutForm

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

# ---------- Cart operations ----------
from django.views.decorators.http import require_POST

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = _get_cart(request)
    pid = str(product_id)
    qty = int(request.POST.get('quantity', 1))
    if pid in cart:
        cart[pid]['quantity'] += qty
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
    return render(request, 'shop/cart.html', {'items': items, 'total': total})

# ---------- Checkout ----------
@login_required
@transaction.atomic
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        return redirect('shop:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            username = request.user.username
            customer, created = Customer.objects.get_or_create(login=username,
                                                               defaults={'full_name': form.cleaned_data['full_name'], 'password': ''})
            status, _ = OrderStatus.objects.get_or_create(name='New')

            order = Orders.objects.create(customer=customer, status=status)
            total = Decimal('0.00')
            for pid, data in cart.items():
                product = get_object_or_404(Product, pk=int(pid))
                qty = int(data['quantity'])
                unit_price = Decimal(data['price'])
                OrderItem.objects.create(order=order, product=product, quantity=qty, unit_price=unit_price)
                try:
                    if product.quantity is not None:
                        product.quantity = max(0, product.quantity - qty)
                        product.save()
                except Exception:
                    pass
                total += unit_price * qty

            request.session.pop(CART_SESSION_ID, None)
            return redirect('shop:order_success', order_id=order.pk)
    else:
        form = CheckoutForm(initial={'full_name': request.user.get_full_name(), 'email': request.user.email})

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
    return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Orders, pk=order_id)
    return render(request, 'shop/order_success.html', {'order': order})

# ---------- Admin tables view ----------
def is_staff_user(u):
    return u.is_active and u.is_staff

@user_passes_test(is_staff_user)
def admin_tables(request):
    products = Product.objects.all()[:500]
    orders = Orders.objects.select_related('customer','status').all()[:500]
    users = AuthUser.objects.all()[:500]
    categories = Category.objects.all()[:200]
    ctx = {
        'products': products,
        'orders': orders,
        'users': users,
        'categories': categories,
    }
    return render(request, 'shop/admin_tables.html', ctx)

def signup(request):
    # простая регистрация через стандартную форму
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # автоматически логиним пользователя
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})