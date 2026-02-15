from django.urls import path, include
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('profile/', views.profile, name='profile'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/success/<int:order_id>/', views.order_success, name='order_success'),

    path('admin-tables/', views.admin_tables_main, name='admin_tables_main'),
    path('admin-tables/customers/', views.admin_customers, name='admin_customers'),
    path('admin-tables/orders/', views.admin_orders, name='admin_orders'),
    path('admin-tables/orders/customer/<int:customer_id>/', views.admin_orders, name='admin_orders_by_customer'),
    path('admin-tables/orders/update-status/<int:order_id>/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-tables/products/', views.admin_products, name='admin_products'),
    path('admin-tables/products/add/', views.admin_add_product, name='admin_add_product'),
    path('admin-tables/products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-tables/statistics/', views.admin_statistics, name='admin_statistics'),
    
    path('signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
]