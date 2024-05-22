from django.shortcuts import render, redirect
from django.contrib.auth  import authenticate, login, logout
from store.models import *
from django.http import JsonResponse
import json
import datetime
from .utils import cookieCart, cartData, guestOrder
from django.contrib import messages


# Create your views here.

def product(request,pk):
    products = Product.objects.get(id=pk)
    context = {'products':products}
    return render(request, 'store/product.html', context)

def contact(request):
    return render(request, 'store/contact.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'store/login.html', {'error': 'Invalid username or password.'})   
    else:
        return render(request, 'store/login.html', {})
    
def user_logout(request):
    logout(request)
    messages.success(request, ("You have been logged out..."))
    return redirect('home')
    

def home(request):

    data = cartData(request)
    cartItems = data['cartItems']
    categories = Category.objects.all()
    products = Product.objects.all()
    sale_products = Product.objects.filter(on_sale=True)
    trending_products =Product.objects.filter(trending=True)
    context = {'categories':categories, 'products':products, 'cartItems':cartItems, 'trending_products':trending_products, 'sale_products':sale_products}
    return render(request, 'store/home.html', context)

def cart(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items':items, 'order':order, 'cartItems':cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items':items, 'order':order, 'cartItems':cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

        total = float(data['form']['total'])
        order.transaction_id = transaction_id

        if total == float(order.get_cart_total):
            order.complete = True
        order.save()

        if order.shipping == True:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['city'],
                state=data['shipping']['state'],
                zipcode=data['shipping']['zipcode'],
            )
    else:
        customer, order = guestOrder(request, data)
    return JsonResponse('Payment submitted..', safe=False)
