from django.shortcuts import render, get_object_or_404
from .models import Product
import json
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from decimal import Decimal
from django.db import transaction
import requests

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {
        'products': products
    })


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    variants = product.variants.all()

    colors = list({v.color for v in variants})
    sizes = list({v.size for v in variants})

    stock_map = {}

    for v in variants:
        key = f"{v.color.lower()}-{v.size.lower()}"
        stock_map[key] = v.stock

    return render(request, 'products/product_detail.html', {
        'product': product,
        'colors': colors,
        'sizes': sizes,
        'stock_map': stock_map
    })

    images = product.images.all()


def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        from .models import ProductVariant

        size = data.get('size', '').strip()

        if not size:
            variant_only = ProductVariant.objects.filter(
                product_id=data['product_id'],
                color__iexact=data['color']
            )

            if variant_only.count() == 1:
                data['size'] = variant_only.first().size

        variant = ProductVariant.objects.filter(
            product_id=data['product_id'],
            color__iexact=data['color'],
            size__iexact=data.get('size', '')
        ).first()

        if not variant:
            return JsonResponse({'error': 'Variante no disponible'}, status=400)

        if variant.stock <= 0:
            return JsonResponse({'error': 'Sin stock'}, status=400)

        cart = request.session.get('cart', [])

        cart.append({
            'product_id': data['product_id'],
            'color': data['color'],
            'size': variant.size,
            'quantity': 1
        })

        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({
            'status': 'ok',
            'cart_count': len(cart)
        })


def cart_view(request):
    cart = request.session.get('cart', [])

    from .models import ProductVariant

    items = []
    total = 0

    for item in cart:
        try:
            variant = ProductVariant.objects.get(
                product_id=item['product_id'],
                color__iexact=item['color'],
                size__iexact=item['size']
            )

            quantity = item.get('quantity', 1)

            items.append({
                'product': variant.product,
                'color': variant.color,
                'size': variant.size,
                'price': variant.price * quantity,
                'quantity': quantity
            })

            total += variant.price * quantity

        except ProductVariant.DoesNotExist:
            print("VARIANTE NO ENCONTRADA:", item)
            continue

    print("ITEMS FINALES:", items)

    return render(request, 'products/cart.html', {
        'items': items,
        'total': total
    })


def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        index = data.get('index')

        cart = request.session.get('cart', [])

        if index is not None and index < len(cart):
            cart.pop(index)

        request.session['cart'] = cart

        return JsonResponse({'status': 'ok'})


def update_cart(request):
    data = json.loads(request.body)

    index = data.get('index')
    change = int(data.get('change'))

    cart = request.session.get('cart', [])

    if index < len(cart):
        cart[index]['quantity'] = cart[index].get('quantity', 1) + change

        if cart[index]['quantity'] <= 0:
            cart.pop(index)

    request.session['cart'] = cart
    return JsonResponse({'status': 'ok'})


def clear_cart(request):
    request.session['cart'] = []
    return JsonResponse({'status': 'ok'})


def checkout_view(request):
    cart = request.session.get('cart', [])

    from .models import ProductVariant

    items = []
    total = 0

    for item in cart:
        try:
            variant = ProductVariant.objects.get(
                product_id=item['product_id'],
                color=item['color'],
                size=item['size']
            )

            quantity = item.get('quantity', 1)

            items.append({
                'product': variant.product,
                'price': variant.price * quantity,
                'quantity': quantity
            })

            total += variant.price * quantity

        except ProductVariant.DoesNotExist:
            continue

    return render(request, 'products/checkout.html', {
        'items': items,
        'total': total
    })

@transaction.atomic
def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)

        cart = request.session.get('cart', [])

        from .models import ProductVariant, Order, OrderItem

        # 🔥 VALIDACIÓN
        if not data.get('name') or not data.get('email') or not data.get('phone'):
            return JsonResponse({'error': 'Faltan datos obligatorios'}, status=400)

        # 🔥 CREAR ORDEN
        order = Order.objects.create(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            document=data.get('document', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            postal_code=data.get('postal_code', ''),
            province=data.get('province', ''),
            shipping=data.get('shipping', ''),
            payment_method=data.get('payment_method', ''),
            total=0
        )

        total = 0

        # 🛍 ITEMS
        for item in cart:
            try:
                variant = ProductVariant.objects.get(
                    product_id=item['product_id'],
                    color=item['color'],
                    size=item['size']
                )
                
                quantity = item.get('quantity', 1)

                if variant.stock < quantity:
                    return JsonResponse({'error': f'Sin stock para {variant.product.name}'}, status=400)

                variant.stock -= quantity
                variant.save()

                price = variant.price * quantity
                total += price

                OrderItem.objects.create(
                    order=order,
                    product_name=variant.product.name,
                    color=variant.color,
                    size=variant.size,
                    quantity=quantity,
                    price=price
                )

            except ProductVariant.DoesNotExist:
                continue

        # 🚚 ENVÍO
        if data.get('shipping') == 'correo':
            total += 9000

        if data.get('payment_method') == 'transfer':
            total = total * Decimal('0.8')

        order.total = total
        order.save()

        # 📧 SOLO SI ES TRANSFERENCIA
        if data.get('payment_method') == "transfer":

            items_text = ""
            for item in order.items.all():
                items_text += f"- {item.product_name} ({item.color}/{item.size}) x{item.quantity} → ${item.price}\n"

            full_message = f"""
Nueva compra

🧍 Cliente: {order.name}
📧 Email: {order.email}
📱 Teléfono: {order.phone}

📍 Dirección: {order.address}
🏙 Ciudad: {order.city}
📮 Código postal: {order.postal_code}
📄 Documento: {order.document}
🏙 Provincia: {order.province}
🚚 Envío: {order.shipping}

🛍 Productos:
{items_text}

💰 Total: ${order.total}
"""

            # 📧 cliente
            send_mail(
                subject='Confirmación de compra',
                message=f"Hola {order.name}, gracias por tu compra!\n\n{full_message}",
                from_email='noapaginaweb@gmail.com',
                recipient_list=[order.email],
                fail_silently=True
            )

            # 📧 dueño
            send_mail(
                subject=f'Nueva venta #{order.id}',
                message=full_message,
                from_email='noapaginaweb@gmail.com',
                recipient_list=['noapaginaweb@gmail.com'],
                fail_silently=True
            )

        return JsonResponse({"order_id": order.id})

    except Exception as e:
        print("ERROR CREATE ORDER:", str(e))
        return JsonResponse({'error': str(e)}, status=500)


def success(request):

    from .models import Order

    order_id = request.GET.get("order_id")

    if order_id:
        try:
            order = Order.objects.get(id=order_id)

            # 👉 solo si fue tarjeta
            if order.payment_method == "card":

                items_text = ""
                for item in order.items.all():
                    items_text += f"- {item.product_name} ({item.color}/{item.size}) x{item.quantity} → ${item.price}\n"

            full_message = f"""
Nueva compra

🧍 Cliente: {order.name}
📧 Email: {order.email}
📱 Teléfono: {order.phone}

📍 Dirección: {order.address}
🏙 Ciudad: {order.city}
📮 Código postal: {order.postal_code}
📄 Documento: {order.document}
🏙 Provincia: {order.province}
🚚 Envío: {order.shipping}

🛍 Productos:
{items_text}

💰 Total: ${order.total}
"""

            send_mail(
                subject='Confirmación de compra',
                message=f"Hola {order.name}, gracias por tu compra!\n\n{full_message}",
                from_email='noapaginaweb@gmail.com',
                recipient_list=[order.email],
                fail_silently=True
            )

            send_mail(
                subject=f'Nueva venta #{order.id}',
                message=full_message,
                from_email='noapaginaweb@gmail.com',
                recipient_list=['noapaginaweb@gmail.com'],
                fail_silently=True
            )

        except Order.DoesNotExist:
            pass

    # limpiar carrito
    request.session['cart'] = []
    request.session.modified = True

    return render(request, 'products/success.html')

def transfer_view(request, order_id):
    from .models import Order

    order = Order.objects.get(id=order_id)

    return render(request, 'products/transfer.html', {
        'order': order
    })

def mobbex_checkout(request, order_id):
    from .models import Order

    order = Order.objects.get(id=order_id)

    url = "https://api.mobbex.com/p/checkout"

    payload = {
        "total": float(order.total),
        "description": f"Pedido #{order.id}",
        "reference": str(order.id),
        "return_url": "http://127.0.0.1:8000/success/",
        "customer": {
            "email": order.email,
            "name": order.name
        }
    }

    headers = {
        "x-api-key": settings.MOBBEX_API_KEY,
        "x-access-token": settings.MOBBEX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    print("MOBBEX RESPONSE:", response.text)  # 🔥 DEBUG

    data = response.json()

    return JsonResponse({
        "url": data.get("data", {}).get("url")
    })


def mobbex_checkout(request, order_id):
    from .models import Order

    order = Order.objects.get(id=order_id)

    url = "https://api.mobbex.com/p/checkout"

    payload = {
        "total": float(order.total),
        "description": f"Pedido #{order.id}",
        "reference": str(order.id),
        "return_url": "http://127.0.0.1:8000/success/",
        "customer": {
            "email": order.email,
            "name": order.name
        }
    }

    headers = {
        "x-api-key": settings.MOBBEX_API_KEY,
        "x-access-token": settings.MOBBEX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    print("MOBBEX RESPONSE:", response.text)

    data = response.json()

    return JsonResponse({
        "url": data.get("data", {}).get("url")
    })