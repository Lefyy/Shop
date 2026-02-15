import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from ..forms import CheckoutForm
from ..services.order_service import create_order
from ..services.cart_service import get_cart, build_cart_items

logger = logging.getLogger(__name__)

@login_required
def checkout(request):
    cart = get_cart(request.session)
    if not cart:
        messages.info(request, "Корзина пуста")
        return redirect("shop:product_list")

    items, total, _ = build_cart_items(cart)
    customer = getattr(request.user, 'customer', None)

    if request.method == 'GET':
        initial = {'address': customer.address} if customer and customer.address else {}
        form = CheckoutForm(initial=initial)
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    # Обработка POST-запроса (подтверждение заказа)
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    if customer is None:
        form.add_error(None, 'Профиль покупателя не найден. Пожалуйста, свяжитесь с администратором.')
        return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})

    try:
        address = form.cleaned_data.get('address', '').strip()
        order = create_order(customer, cart, address)
        request.session.pop("cart", None)
        return redirect("shop:order_success", order_id=order.pk)
        
    except ValueError as e:
        form.add_error(None, str(e))
    except Exception:
        logger.exception("Checkout failed")
        form.add_error(None, "Ошибка оформления заказа. Попробуйте позже.")
        
    return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})