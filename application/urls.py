# from django.contrib import admin
# from django.urls import path, include
from application import views

from django.urls import path,include

urlpatterns = [
    # Authentication Routes
    path('', views.login_user, name='login'),
    path('register/', views.register, name='register'),
    path('user/', views.user, name='user'),

    # General User Routes
    path('index/', views.index, name='index'),
    path('contact/', views.contact, name='contact'),


    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),



    path('shop/', views.shop, name='shop'),
    path('detail/', views.detail, name='detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('terms/', views.terms, name='terms'),

    # path('products/', views.products, name='products'),
    path('products/', views.products, name='products'),
    path('admin/', views.login_user, name='login'),
    path('admin_register/', views.admin_register, name='admin_register'),
    path('admin_customer/', views.admin_customer, name='admin_customer'),
    path('admin_data/', views.admin_data, name='admin_data'),
    path('customer_data/', views.customer_data, name='customer_data'),
    path('category/', views.category, name='category'),
    path('category_data/', views.category_data, name='category_data'),
    path('categories/update/<int:id>/', views.update_category, name='update_category'),
    path('categories/delete/<int:id>/', views.delete, name='delete'),

    path('product_data/', views.product_data, name='product_data'),
    path('products/update/<int:pk>/', views.update_product, name='update_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),


    path('shop/', views.shop_view, name='shop'),
    path('shop/category/<int:category_id>/', views.shop_view, name='shop_category'),
    path('shop/subcategory/<int:subcategory_id>/', views.shop_view, name='shop_subcategory'),



    # Promo code
    path('code/', views.promocode, name='promocode'),
    path('promo/promotype/', views.promotype, name='promotype'),

]

