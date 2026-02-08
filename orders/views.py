import datetime
import uuid
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse

from carts.models import Cart, CartItem
from orders.forms import OrderForm
from orders.models import Order, OrderProduct, Payment



from django.http import HttpResponse

def payments(request):
    payment_success = False

    if request.method == 'POST' and request.user.is_authenticated:

        # get latest order of this user
        order = Order.objects.filter(
            user=request.user,
            is_ordered=False
        ).last()

        if order:
            # mark order as completed
            order.is_ordered = True
            order.save()

            # OPTIONAL: create payment record
            payment = Payment(
                user=request.user,
                payment_id=str(uuid.uuid4()),
                payment_method='COD',  # or Razorpay / Stripe
                amount_paid=order.order_total,
                status='Completed',
            )
            payment.save()

            # clear cart items
            CartItem.objects.filter(user=request.user).delete()

            payment_success = True

    return render(request, 'orders/payments.html', {
        'payment_success': payment_success
    })

# Create your views here.
def place_order(req, total=0, quantity=0):
    if not req.user.is_authenticated:
        return redirect('login')

    current_user = req.user
    cart_items = CartItem.objects.filter(user=current_user)

    if cart_items.count() <= 0:
        return redirect('store')

    tax = 0
    grand_total = 0

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if req.method == 'POST':
        form = OrderForm(req.POST)
        if form.is_valid():

            # 1️⃣ CREATE ORDER
            order = Order()
            order.user = current_user
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address_line_1 = form.cleaned_data['address_line_1']
            order.address_line_2 = form.cleaned_data['address_line_2']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.order_note = form.cleaned_data['order_note']
            order.order_total = grand_total
            order.tax = tax
            order.ip = req.META.get('REMOTE_ADDR')
            order.is_ordered = True   # ✅ VERY IMPORTANT
            order.save()

            # 2️⃣ GENERATE ORDER NUMBER
            current_date = datetime.date.today().strftime("%Y%m%d")
            order.order_number = current_date + str(order.id)
            order.save()

            # 3️⃣ CREATE ORDER PRODUCTS
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order = order
                order_product.user = current_user
                order_product.product = item.product
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

                # save variations
                order_product.variations.set(item.variations.all())
                order_product.save()

            # 4️⃣ CLEAR CART
            cart_items.delete()

            # 5️⃣ REDIRECT TO ORDER DETAIL
            return redirect('order_detail', order_number=order.order_number)

    return redirect('checkout')
def order_complete(request):
    order = Order.objects.filter(user=request.user, is_ordered=True).last()
    return render(request, 'orders/order_complete.html', {'order': order})

def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)