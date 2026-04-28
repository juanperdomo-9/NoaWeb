from django.urls import path
from .views import product_list, product_detail, add_to_cart, cart_view, remove_from_cart, update_cart, clear_cart, checkout_view, success, create_order, transfer_view, mobbex_checkout

urlpatterns = [
    path('', product_list, name='product_list'),
    path('product/<int:id>/', product_detail, name='product_detail'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart_view'),
    path('remove-from-cart/', remove_from_cart),
    path('update-cart/', update_cart),
    path('clear-cart/', clear_cart),
    path('checkout/', checkout_view, name='checkout_view'),
    path('success/', success, name='success'),
    path('create-order/', create_order, name='create_order'),
    path('transfer/<int:order_id>/', transfer_view, name='transfer'),
    path('mobbex/<int:order_id>/', mobbex_checkout, name='mobbex_checkout'),
]