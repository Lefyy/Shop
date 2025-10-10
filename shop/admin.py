from django.contrib import admin
from .models import Product, Category, Orders, OrderItem, OrderStatus, Customer

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'quantity', 'category')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name')

@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'created_date', 'status')
    search_fields = ('customer__full_name',)
    list_filter = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price')

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('id','name')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id','full_name','login')
    search_fields = ('full_name','login')