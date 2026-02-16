# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(unique=True, max_length=255)

    class Meta:
        db_table = 'category'

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'customer'


class OrderItem(models.Model):
    order = models.ForeignKey('Orders', models.CASCADE)
    product = models.ForeignKey('Product', models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_item'

    @property
    def total_price(self):
        return self.quantity * self.unit_price


class OrderStatus(models.Model):
    name = models.CharField(unique=True, max_length=255)

    class Meta:
        db_table = 'order_status'


class Orders(models.Model):
    customer = models.ForeignKey(Customer, models.PROTECT)
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey(OrderStatus, models.PROTECT)

    class Meta:
        db_table = 'orders'


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    category = models.ForeignKey(Category, models.PROTECT)
    image = models.ImageField(upload_to="products/%Y/%m/%d/", blank=True, null=True)

    class Meta:
        db_table = 'product'