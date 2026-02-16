from decimal import Decimal
from ..models import Product

CART_SESSION_ID = "cart"

def get_cart(session):
    return session.setdefault(CART_SESSION_ID, {})

def save_cart(session, cart):
    session[CART_SESSION_ID] = cart
    session.modified = True

def add_product(session, product, quantity):
    cart = get_cart(session)
    pid = str(product.id)
    
    if quantity <= 0:
        return False, "Некорректное количество"

    current_qty = cart.get(pid, 0)
    new_qty = current_qty + quantity
    
    # Проверка доступного количества
    if product.quantity is not None and new_qty > product.quantity:
        new_qty = product.quantity

    if new_qty <= 0:
        return False, "Недостаточно товара"
        
    cart[pid] = new_qty
    save_cart(session, cart)
    return True, "Добавлено"

def remove_product(session, product_id):
    cart = get_cart(session)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        save_cart(session, cart)

def update_product_quantity(session, product, new_qty):
    cart = get_cart(session)
    pid = str(product.id)
    
    if new_qty <= 0:
        remove_product(session, product.id)
        return True, "Удалено"
        
    if product.quantity is not None and new_qty > product.quantity:
        cart[pid] = product.quantity
        save_cart(session, cart)
        return True, f"Уменьшено до доступного ({product.quantity})"
        
    if cart.get(pid) != new_qty:
        cart[pid] = new_qty
        save_cart(session, cart)
        return True, "Обновлено"
        
    return False, "Без изменений"

def build_cart_items(cart):
    product_ids = list(cart.keys())
    products = Product.objects.in_bulk([int(i) for i in product_ids])

    items = []
    total = Decimal("0.00")

    for pid, qty in cart.items():
        product = products.get(int(pid))
        if not product:
            continue

        subtotal = product.price * qty
        total += subtotal

        items.append({
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": qty,
            "subtotal": subtotal,
        })

    return items, total, products