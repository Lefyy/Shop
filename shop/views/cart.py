import logging
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from ..models import Product
from ..services.cart_service import (
    add_product, get_cart, build_cart_items, remove_product, update_product_quantity
)

logger = logging.getLogger(__name__)

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    qty = int(request.POST.get("quantity", 1))
    
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
            product = Product.objects.get(id=pid)
            
            changed, msg = update_product_quantity(request.session, product, qty)
            if changed:
                any_changes = True
                if msg != "Удалено" and msg != "Обновлено":
                    messages.warning(request, msg)
                    
        except (ValueError, TypeError, Product.DoesNotExist):
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