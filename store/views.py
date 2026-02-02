from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404
from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from .models import Product
from django.db.models import Q
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
# Create your views here.
def store(req ,category_slug=None):
    categories=None
    products=None
    if category_slug != None: #selecting for category
        categories=get_object_or_404(Category,slug=category_slug)
        products=Product.objects.filter(category=categories,is_available=True)
        paginator= Paginator(products,1)#all 6 products will show in store
        page=req.GET.get('page')
        paged_products=paginator.get_page(page)
        product_count=products.count()
    else:#for all products
         products=Product.objects.all().filter(is_available=True).order_by('id')
         paginator= Paginator(products,3)#all 6 products will show in store
         page=req.GET.get('page')
         paged_products=paginator.get_page(page)
         product_count=products.count()


   
    context={
        'products':paged_products,
        'product_count': product_count,
    }
    return render(req,'store/store.html',context)


def product_detail(req,category_slug,product_slug):
    try:
        single_product=Product.objects.get(category__slug=category_slug,slug=product_slug) #to get categories slug
        in_cart=CartItem.objects.filter(cart__cart_id=_cart_id(req),product=single_product).exists() #true or false for add to cart i=for single item
    except Exception as e:
        raise e
    

    context={
        "single_product":single_product,
        'in_cart':in_cart,
    }
    return render(req,'store/product_detail.html',context)


def search(req):
    if 'keyword' in req.GET: #if there is value in keyword
        keyword=req.GET['keyword'] #then we will be store in  variable keyword
        if keyword:#if keyword is not blank
            products=Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword) )#it will found in desc related to keyword  and Q is used for query set we cant use or operator directly it will break the code
            product_count=products.count()
    
    context={
        'products':products,
        'product_count':product_count,
    }

    return render(req,'store/store.html' ,context)


