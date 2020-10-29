import urllib
from rest_framework.decorators import api_view, permission_classes
from user.models import Person;
from django.http import JsonResponse
import uuid
from django.http import HttpResponseRedirect
from django.views import View
from django.conf import settings
from django.shortcuts import redirect
import requests
from django.views.generic import DetailView
import stripe
import json
# Create your views here.
import hashlib




@api_view(["GET"])
def user(request,userid):
    person = Person.objects.get(id=userid)
    personDict = {};
    personDict["email"] = person.email;
    personDict["password"] = person.pwd;
    personDict["is_user"] = person.is_user;
    personDict["is_coach"] = person.is_coach;


    response = JsonResponse(personDict,safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getCurrentUer(request):
    person = Person.objects.get(id=request.session['user_id'])
    personDict = {};
    personDict["email"] = person.email;
    personDict["password"] = person.pwd;
    personDict["is_user"] = person.is_user;
    personDict["is_coach"] = person.is_coach;


    response = JsonResponse(personDict,safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getAllUser(request):
    persons = Person.objects.all()
    role = request.GET.get('role', "all")
    personResult = {}
    personlList = []

    for person in persons:
        personDict = {};
        personDict["email"] = person.email;
        personDict["password"] = person.pwd;
        personDict["is_user"] = person.is_user;
        personDict["is_coach"] = person.is_coach;
        if(role == "all"):
            personlList.append(personDict)
        else:
            if(role == "client"):
                if(person.is_user == True and person.is_coach == False):
                    personlList.append(personDict)
            if (role == "admin"):
                if (person.is_user == True and person.is_coach == True):
                    personlList.append(personDict)
            if (role == "coach"):
                if (person.is_user == False and person.is_coach == True):
                    personlList.append(personDict)
    personResult["result"] = personlList;


    response = JsonResponse(personResult,safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def deleteUser(request,userid):
    person = Person.objects.get(id=userid)
    person.delete()

    response = JsonResponse({"succeess": True},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["POST"])
def createUser(request):

    firstname = request.data['firstname']
    lastname = request.data['lastname']
    email = request.data['email']
    password = hashlib.md5(request.data['password'].encode('utf-8')).hexdigest()

    if(request.data['role'] == "client"):
        is_user = True;
        is_coach = False;
    if (request.data['role'] == "admin"):
        is_user = True;
        is_coach = True;
    if (request.data['role'] == "coach"):
        is_user = False;
        is_coach = True;

    person = Person( email=email,pwd=password, is_user=is_user,is_coach=is_coach)
    person.save()

    response = JsonResponse({"id" : person.id},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response


def logout(request):
    respDict = {};
    respDict["logout"] = True;

    response = JsonResponse(respDict, safe=False);
    try:
        response.delete_cookie('sessionid')
        del request.session['email']
        del request.session['password']
        del request.session['authenticated']
        del request.session['user_id']
    except:
        pass



    return response


class StripeAuthorizeView(View):

    def get(self, request):

        url = 'https://connect.stripe.com/oauth/authorize'
        params = {
            'response_type': 'code',
            'scope': 'read_write',
            'client_id': settings.STRIPE_CONNECT_CLIENT_ID,
            'redirect_uri': f'http://localhost:8000/api/user/oauth/callback/'
        }
        url = f'{url}?{urllib.parse.urlencode(params)}'
        return redirect(url)

class StripeAuthorizeCallbackView(View):

    def get(self, request):
        code = request.GET.get('code')
        if code:
            data = {
                'client_secret': settings.STRIPE_SECRET_KEY,
                'grant_type': 'authorization_code',
                'client_id': settings.STRIPE_CONNECT_CLIENT_ID,
                'code': code
            }
            url = 'https://connect.stripe.com/oauth/token'
            resp = requests.post(url, params=data)
            # add stripe info to the seller
            stripe_user_id = resp.json()['stripe_user_id']
            stripe_access_token = resp.json()['access_token']
            seller = Person.objects.filter(id=request.session['user_id']).first()
            seller.stripe_access_token = stripe_access_token
            seller.stripe_user_id = stripe_user_id
            seller.save()

        return HttpResponseRedirect("http://localhost:3000/#/dashboard?authorized=true")

class PersonDetailView(DetailView):
    model = Person
    template_name = 'user/user_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(PersonDetailView, self).get_context_data(*args, **kwargs)
        context['key'] = settings.STRIPE_PUBLISHABLE_KEY
        return context

    def render_to_response(self, context, **response_kwargs):
        return super(PersonDetailView, self).render_to_response(context, **response_kwargs)

class UserChargeView(View):

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        json_data = json.loads(request.body)
        person = Person.objects.filter(id=json_data['person_id']).first()
        fee_percentage = .01 * int(10) #person fee is 10 dollar
        try:
            customer = get_or_create_customer(
                request.session['email'],
                json_data['token'],
                person.stripe_access_token,
                person.stripe_user_id,
            )
            charge = stripe.Charge.create(
                amount=json_data['amount'],
                currency='usd',
                customer=customer.id,
                description=json_data['description'],
                application_fee=int(json_data['amount'] * fee_percentage),
                stripe_account=person.stripe_user_id,
            )
            if charge:
                return JsonResponse({'status': 'success'}, status=202)
        except stripe.error.StripeError as e:
            return JsonResponse({'status': 'error'}, status=500)

def get_or_create_customer(email, token, stripe_access_token, stripe_account):
    stripe.api_key = stripe_access_token
    connected_customers = stripe.Customer.list()
    for customer in connected_customers:
        if customer.email == email:
            print(f'{email} found')
            return customer
    print(f'{email} created')
    return stripe.Customer.create(
        email=email,
        source=token,
        stripe_account=stripe_account,
    )
