
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from accounts.models import Account, UserProfile
from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order, OrderProduct
from store.models import ReviewRating
from .forms import RegistrationForm, UserForm,UserProfileForm
from django.contrib import messages ,auth
from django.contrib.auth.decorators import login_required

#verfication email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage



import requests
# Create your views here.
def register(req):
    if req.method=='POST':
        form=RegistrationForm(req.POST)
        if form.is_valid():#when u use the django form we have to use clean data to fetch  the data 
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            phone_number=form.cleaned_data['phone_number']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            user_name=email.split("@")[0]
            user=Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,user_name=user_name,password=password)
            user.phone_number=phone_number
            user.save()

            #user Activation[after we save user object]
            current_site=get_current_site(req)
            mail_subject="Please activate your account"
            message=render_to_string('accounts/account_verfication.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])

            try:
                send_email.send()
            except Exception as e:
                print("Email failed:", e)

            # messages.success(req,'Thank you for registering with us. We have sent you verification link to your email address please verify it!')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form=RegistrationForm()
    context={
        'form':form,
    }
    return render(req,'accounts/register.html',context)

def login(req):
    if req.method=='POST':
        email=req.POST['email']
        password=req.POST['password']

        user=auth.authenticate(email=email,password=password)
        if user is not None:
            try:
                cart=Cart.objects.get(cart_id=_cart_id(req))
                is_cart_item_exists=CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item=CartItem.objects.filter(cart=cart)

                    #getting product variation
                    product_variation=[]
                    for item in cart_item:
                        variations=item.variations.all()
                        product_variation.append(list(variations))

                    #get the cart items from  the user to acess his product variations
                    cart_item=CartItem.objects.filter(user=user)
                    ex_var_list=[]
                    id=[]
                    for item in cart_item:
                        existing_variation=item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index=ex_var_list.index(pr)
                            item_id=id[index]
                            item=CartItem.objects.get(id=item_id)
                            item.quantity+=1
                            item.user=user
                            item.save()
                        else:
                            cart_item=CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                    item.user=user
                                    item.save()
            except:
                pass
            auth.login(req,user)
            messages.success(req,'You are Now Logged In')
            url=req.META.get('HTTP_REFERER')#prev url where u came
            try:
                query=requests.utils.urlparse(url).query
             
                #next=/cart/checkout/
                params=dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage=params['next']
                    return redirect(nextPage)
                
            except:
                return redirect('dashboard')
        else:
            messages.error(req,'Invalid login credentials ')
            return redirect('login')
    return render(req,'accounts/login.html')


@login_required(login_url='login')
def logout(req):
    auth.logout(req)
    messages.success(req,'You are Logged Out')
    return redirect('login')


def activate(req,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(req,'congratulation! your account is activated')
        return redirect('login')
    else:
        messages.error(req,'Invalid activation Link')
        return redirect('register')


@login_required(login_url='login') 
def dashboard(req):
    orders_count = Order.objects.filter(user=req.user).count()
    reviews_count = ReviewRating.objects.filter(user=req.user).count()

    userprofile=UserProfile.objects.get(user_id=req.user.id)
    context = { 
        'orders_count': orders_count,
        'reviews_count': reviews_count,
        'userprofile':userprofile
    }
    return render(req, 'accounts/dashboard.html', context)

def forgotPassword(req):
    if req.method=='POST':
        email=req.POST['email']
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__exact=email)
            #reset password email
            current_site=get_current_site(req)
            mail_subject="Reset Your Password"
            message=render_to_string('accounts/reset_password_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
        
            messages.success(req,'Password reset  email has been sent to your email address')
            return redirect('login')
        else:
            messages.error(req,'Account Does Not Exist!')
            return redirect('forgotPassword')
    return render(req,'accounts/forgotPassword.html')


def resetpassword_validate(req ,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user,token):
        req.session['uid']=uid
        messages.success(req,'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(req,'This link is expired')
        return redirect('login')
    
def resetPassword(req):
    if req.method=='POST':
        password=req.POST['password']
        confirm_password=req.POST['confirm_password']

        if password == confirm_password:
            uid=req.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(req,'Password Successful')
            return redirect('login')
        else:
            messages.error(req,'password do not match ')
            return redirect('resetPassword')
    else:
        return render(req,'accounts/resetPassword.html')
    

def my_orders(req):
    orders = Order.objects.filter(
        user=req.user,
        is_ordered=True
    ).order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(req, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(user_name__exact=request.user.user_name)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    ordered_products = OrderProduct.objects.filter(order=order)

    context = {
        'order': order,
        'ordered_products': ordered_products,
    }
    return render(request, 'accounts/order_detail.html', context)
