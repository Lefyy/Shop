from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

# Create your tests here.
from shop.models import Category, Customer, OrderItem, Orders, OrderStatus, Product
from shop.services import cart_service
from shop.services.order_service import create_order


class SessionMock(dict):
    def __init__(self):
        super().__init__()
        self.modified = False


class CartServiceTests(TestCase):
    def setUp(self):
        self.session = SessionMock()
        self.category = Category.objects.create(name="Fruits")
        self.product = Product.objects.create(
            name="Apple",
            price=Decimal("10.50"),
            quantity=5,
            category=self.category,
        )

    def test_add_product_rejects_non_positive_quantity(self):
        ok, message = cart_service.add_product(self.session, self.product, 0)

        self.assertFalse(ok)
        self.assertEqual(message, "Некорректное количество")
        self.assertEqual(self.session.get(cart_service.CART_SESSION_ID, {}), {})

    def test_add_product_caps_quantity_by_stock(self):
        cart_service.add_product(self.session, self.product, 3)
        ok, message = cart_service.add_product(self.session, self.product, 10)

        self.assertTrue(ok)
        self.assertEqual(message, "Добавлено")
        self.assertEqual(self.session[cart_service.CART_SESSION_ID][str(self.product.id)], 5)
        self.assertTrue(self.session.modified)

    def test_update_product_quantity_to_zero_removes_item(self):
        cart_service.add_product(self.session, self.product, 2)

        ok, message = cart_service.update_product_quantity(self.session, self.product, 0)

        self.assertTrue(ok)
        self.assertEqual(message, "Удалено")
        self.assertNotIn(str(self.product.id), self.session[cart_service.CART_SESSION_ID])

    def test_build_cart_items_calculates_total_and_skips_missing_products(self):
        missing_product_id = self.product.id + 100
        cart = {str(self.product.id): 2, str(missing_product_id): 3}

        items, total, products = cart_service.build_cart_items(cart)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["product_id"], self.product.id)
        self.assertEqual(items[0]["subtotal"], Decimal("21.00"))
        self.assertEqual(total, Decimal("21.00"))
        self.assertNotIn(missing_product_id, products)


class CreateOrderServiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Vegetables")
        self.product = Product.objects.create(
            name="Cucumber",
            price=Decimal("99.90"),
            quantity=10,
            category=self.category,
        )
        user = get_user_model().objects.create_user(username="buyer", password="pass12345")
        self.customer = Customer.objects.create(user=user, address="Old address")

    def test_create_order_updates_stock_and_customer_address(self):
        order = create_order(
            customer=self.customer,
            cart={str(self.product.id): 3},
            address="New address",
        )

        self.product.refresh_from_db()
        self.customer.refresh_from_db()
        item = OrderItem.objects.get(order=order, product=self.product)

        self.assertIsInstance(order, Orders)
        self.assertEqual(order.status.name, "Создан")
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.unit_price, Decimal("99.90"))
        self.assertEqual(self.product.quantity, 7)
        self.assertEqual(self.customer.address, "New address")
        self.assertTrue(OrderStatus.objects.filter(name="Создан").exists())

    def test_create_order_raises_for_insufficient_stock_and_rolls_back(self):
        with self.assertRaisesMessage(ValueError, "доступно только 10"):
            create_order(customer=self.customer, cart={str(self.product.id): 20})

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 10)
        self.assertEqual(Orders.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
