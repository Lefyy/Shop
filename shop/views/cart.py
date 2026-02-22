import logging
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages

from ..models import Product
from ..selectors.cart_selectors import get_product_by_id_or_404, get_product_by_id
from ..services.cart_service import (
    add_product, get_cart, build_cart_items, remove_product, update_product_quantity
)

logger = logging.getLogger(__name__)

@require_POST
def add_to_cart(request, product_id):
    product = get_product_by_id_or_404(product_id)
    raw_quantity = request.POST.get("quantity", 1)

    try:
        qty = int(raw_quantity)
    except (TypeError, ValueError):
        messages.warning(request, "Некорректное количество товара.")
        return redirect("shop:view_cart")

    if qty < 1:
        messages.warning(request, "Количество должно быть не меньше 1.")
        return redirect("shop:view_cart")

    if product.quantity is not None and product.quantity <= 0:
        messages.info(request, "Товар временно отсутствует на складе.")
        return redirect("shop:view_cart")

    if product.quantity is not None and qty > product.quantity:
        qty = product.quantity
        messages.info(request, f"Количество ограничено доступным остатком ({product.quantity}).")
    
    add_product(request.session, product, qty)
    return redirect("shop:view_cart")

def remove_from_cart(request, product_id):
    remove_product(request.session, product_id)
    return redirect("shop:view_cart")

@require_POST
def update_cart(request):
    cart = get_cart(request.session)
    if not cart:
        messages.info(request, "Корзина пуста.")
        return redirect('shop:view_cart')

    any_changes = False
    
    for key, value in request.POST.items():
        if not key.startswith('quantity_'):
            continue
            
        try:
            pid = int(key.split('_', 1)[1])
            qty = int(value)
            product = get_product_by_id(pid)
            
            if product.quantity is not None and qty > product.quantity:
                messages.info(request, f"Количество для «{product.name}» ограничено доступным остатком ({product.quantity}).")

            changed, msg = update_product_quantity(request.session, product, qty)
            if changed:
                any_changes = True
                if msg != "Удалено" and msg != "Обновлено":
                    messages.warning(request, msg)
                    
        except (ValueError, TypeError):
            messages.warning(request, "Некорректное количество товара.")
            continue
        except Product.DoesNotExist:
            messages.info(request, "Один из товаров уже недоступен.")
            continue

    if any_changes:
        messages.success(request, "Корзина обновлена.")
    else:
        messages.info(request, "Изменений не обнаружено.")

    return redirect('shop:view_cart')

def view_cart(request):
    cart = get_cart(request.session)
    items, total, product_dict = build_cart_items(cart)

    return render(request, "shop/cart.html", {
        "items": items,
        "total": total,
        "product_dict": product_dict
    })