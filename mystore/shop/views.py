from django.shortcuts import render
from django.http import HttpResponse
from .models import Product,Contact,Orders,OrderUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from .PayTm import checksum
MERCHANT_KEY = 'kbzk1DSbJiV_O3p5';


# Create your views here.


def index(request):
    # products = Product.objects.all()
    # print(products)
    # n = len(products)
    # nSlides = n//4 + ceil((n/4)-(n//4))

    allProds = []
    catprods = Product.objects.values('category', 'id')

    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides':nSlides, 'range': range(1,nSlides),'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)

def searchMatch(query,item):
    '''Return only when query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    # products = Product.objects.all()
    # print(products)
    # n = len(products)
    # nSlides = n//4 + ceil((n/4)-(n//4))

    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod_temp  = Product.objects.filter(category=cat)
        prod = [item for item in prod_temp if searchMatch(query,item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides':nSlides, 'range': range(1,nSlides),'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds':allProds, 'msg':""}
    if len(allProds)==0 or len(query)<4:
        params= {'msg': "Please make sure to enter relevent search query."}

    return render(request, 'shop/search.html', params)


def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    thank = False
    if request.method == "POST":
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        desc = request.POST.get('desc','')
        print(name,email,phone,desc)
        contact = Contact(name=name,email = email, phone = phone, desc= desc )
        contact.save()
        thank = True

    return render(request,'shop/contact.html', {'thank': thank})


def trackers(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId','')
        email = request.POST.get('email','')
        try:
            order = Orders.objects.filter(order_id = orderId, email = email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id = orderId)
                updates = []
                for item in update:
                    updates.append({'text':item.update_desc, 'time':item.timestamp})
                    response = json.dumps({"status": "success", "updates":updates, "itemsJson":order[0].items_json},
                                          default = str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status": "noitem"}')
        except Exception as e:
            return HttpResponse('{"status": "error"}')

    return render(request,'shop/trackers.html')


def productview(request, myid):
    #fetch the product using ID
    prod = Product.objects.filter(id=myid)
    return render(request, 'shop/prodview.html',{'product': prod[0]})


def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        number = request.POST.get('phone', '')
        amount = request.POST.get('amount', '')
        print(name, email, address, city, state, zip_code, number, items_json, amount)
        order = Orders(items_json = items_json, name=name, email=email, address=address, city=city, state=state,
                       zip_code=zip_code, number=number, amount=amount)
        order.save()

        update = OrderUpdate(order_id = order.order_id, update_desc= 'The order has been placed!')
        update.save()

        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank': thank, 'id': id})
        #request Your user to trasfer the amount to your account
        param_dict = {
            'MID': 'WorldP64425807474247',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': str(email),
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',
        }

        param_dict['CHECKSUMHASH'] = checksum.generate_checksum(param_dict,MERCHANT_KEY)
        return render(request, 'shop/checkout.html',{'param_dict':param_dict})
    return render(request,'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    # PayTm will send you POST request here ==>
    return HttpResponse('Done')

    pass