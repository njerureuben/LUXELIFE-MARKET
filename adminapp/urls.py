from . import views
from django.urls import path

urlpatterns = [
    # Admin Login Page
    path('admin/login/', views.adminsignin, name='adminsignin'),

    # Dashboard Data
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Users
    path('admin/create/admin', views.createadmin, name='createadmin'),
    path('admin/add/customer/', views.createcustomer, name='createcustomer'),
    path('admin/data', views.admindata, name='admindata'),
    path('admin/customer/data/', views.customerdata, name='customerdata'),
    path('admin/delete/<int:pk>/', views.deleteadmin, name='deleteadmin'),
    path('admin/update/<int:pk>/', views.adminupdate, name='adminupdate'),

    # Products
    path('admin/products/', views.productsdata, name='productsdata'),
    path('admin/categories/', views.categorydata, name='categorydata'),
    path('admin/add/products/', views.adminproducts, name='adminproducts'),
    path('admin/add/categories/', views.admincategory, name='admincategory'),
    path('admin/delete/products/<int:pk>/', views.admindeleteproduct, name='admindeleteproduct'),
    path('admin/update/products/<int:pk>/', views.adminupdateproduct, name='adminupdateproduct'),
    path('admin/update/categories/<int:id>/', views.adminupdatecategory, name='adminupdatecategory'),
]
