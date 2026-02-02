from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.core.exceptions import ObjectDoesNotExist
from carts.models import Cart, CartItem
from store.models import Product, Variation

# Create your views here.


def _cart_id(req):
    cart=req.session.session_key
    if not cart:    
        cart=req.session.create()
    return cart



def add_cart(req, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variation = []

    # 1️⃣ Collect variations from POST
    if req.method == 'POST':
        for key, value in req.POST.items():
            if key == 'csrfmiddlewaretoken':
                continue

            value = value.strip()

            variations = Variation.objects.filter(
                product=product,
                variation_category__iexact=key,
                variation_value__iexact=value
            )

            if variations.exists():
                product_variation.append(variations.first())

    # 2️⃣ Get or create cart
    cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(req))

    # 3️⃣ Check existing cart items (same product)
    cart_items = CartItem.objects.filter(product=product, cart=cart)
    found = False

    for item in cart_items: 
        if set(item.variations.all()) == set(product_variation):
            item.quantity += 1
            item.save()
            found = True
            break

    # 4️⃣ Create new cart item if variation combo not found
    if not found:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )
        if product_variation:
            cart_item.variations.set(product_variation)
        cart_item.save()

    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax=0
        grand_total=0
        cart_obj = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        tax=(2 * total)/100 #2percent   
        grand_total=total+tax

    except ObjectDoesNotExist:
        pass #just ignore 

    context={
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'grand_total':grand_total,
        'tax':tax
    }


    return render(request,'store/cart.html',context)

#decrement of quanitity
def remove_cart(req,product_id,cart_item_id):
    cart=Cart.objects.get(cart_id=_cart_id(req)) #private variable
    product=get_object_or_404(Product,id=product_id)
    try:

        cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
        if cart_item.quantity>1: # if its greater then one it will decrement
            cart_item.quantity-=1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

#removing the item directly
def remove_cart_item(req,product_id,cart_item_id):
    cart=Cart.objects.get(cart_id=_cart_id(req))
    product=get_object_or_404(Product,id=product_id)
    cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cart')