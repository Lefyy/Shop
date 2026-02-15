from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from shop.selectors.order_selectors import get_order_for_user


@login_required
def order_success(request, order_id):
    order = get_order_for_user(
        order_id=order_id,
        customer=request.user.customer
    )

    return render(request, "shop/order_success.html", {
        "order": order
    })