import datetime
import uuid
from django.shortcuts import redirect, render
from django.http import HttpResponse

from carts.models import Cart, CartItem
from orders.forms import OrderForm
from orders.models import Order, OrderProduct, Payment



from django.http import HttpResponse

def payments(request):
    payment_success = False

    if request.method == 'POST':

        # delete user-based cart items
        if request.user.is_authenticated:
            CartItem.objects.filter(user=request.user).delete()

        # delete session-based cart items
        cart_id = request.session.session_key
        if cart_id:
            CartItem.objects.filter(cart__cart_id=cart_id).delete()

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
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = req.META.get('REMOTE_ADDR')
            data.save()

            # generate order number
            current_date = datetime.date.today().strftime("%Y%m%d")
            data.order_number = current_date + str(data.id)
            data.save()

            order = data  # ✅ IMPORTANT

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }

            return render(req, 'orders/payments.html', context)

    return redirect('checkout')

def order_complete(request):
    order = Order.objects.filter(user=request.user, is_ordered=True).last()
    return render(request, 'orders/order_complete.html', {'order': order})
