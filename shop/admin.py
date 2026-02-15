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
    search_fields = (
        'customer__user__username',
        'customer__user__email',
    )
    list_filter = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price')

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('id','name')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'full_name', 'email')
    search_fields = ('user__username', 'user__email')

    def username(self, obj):
        return obj.user.username
    username.admin_order_field = 'user__username'

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.admin_order_field = 'user__first_name'

    def email(self, obj):
        return obj.user.email
    email.admin_order_field = 'user__email'