import urllib
from rest_framework.decorators import api_view, permission_classes
from user.models import Person;
from user.models import StripePaymentDetail;
from django.http import JsonResponse
from user.models import ClientProfile;
from user.models import CoachProfile;
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
import json
import  os
import re
from django.middleware.csrf import get_token




def csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})


def getCurrentUserInfo(request):
    userInfo = {}
    userInfo['email'] = request.session['email']
    userInfo['password'] = request.session['password']
    userInfo['user_id'] = request.session['user_id']
    userInfo['authenticated'] = request.session['authenticated']
    return userInfo;


@api_view(["GET"])
def user(request,userid):
    person = Person.objects.get(id=userid)
    personDict = {};
    personDict["email"] = person.email;
    personDict["password"] = person.pwd;
    personDict["is_user"] = person.is_user;
    personDict["is_coach"] = person.is_coach;
    personDict["vname"] = person.vname;
    personDict["nname"] = person.nname;


    response = JsonResponse(personDict,safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getCurrentUer(request):
    person = Person.objects.get(id=getCurrentUserInfo(request)['user_id'])
    personDict = {};
    personDict["user_id"] = person.id;
    personDict["email"] = person.email;
    personDict["password"] = person.pwd;
    personDict["is_user"] = person.is_user;
    personDict["is_coach"] = person.is_coach;
    personDict["vname"] = person.vname;
    personDict["nname"] = person.nname;
    personDict["profilepic"] = ""
    personDict["price"] = ""


    if person.is_user == 1 and person.is_coach == 0:
        personProfile = ClientProfile.objects.filter(person_id=getCurrentUserInfo(request)['user_id']).first()
        if personProfile:
            personDict["profilepic"] = personProfile.profile_pic;
    elif person.is_user == 0 and person.is_coach == 1:
        coachProfile = CoachProfile.objects.filter(person_id=getCurrentUserInfo(request)['user_id']).first()
        if coachProfile:
            personDict["profilepic"] = coachProfile.profile_pic;
            personDict["price"] = coachProfile.price;


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
        personDict["id"] = person.id;
        personDict["password"] = person.pwd;
        personDict["is_user"] = person.is_user;
        personDict["is_coach"] = person.is_coach;
        personDict["vname"] = person.vname;
        personDict["nname"] = person.nname;

        if person.is_user == 1 and person.is_coach == 0:
            personProfile = ClientProfile.objects.filter(person_id=person.id).first()
            if personProfile:
                personDict["profilepic"] = personProfile.profile_pic;
        elif person.is_user == 0 and person.is_coach == 1:
            coachProfile = CoachProfile.objects.filter(person_id=person.id).first()
            if coachProfile:
                personDict["profilepic"] = coachProfile.profile_pic;
                personDict["price"] = coachProfile.price;



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
def updateUserProfile(request):
    person = Person.objects.get(id=getCurrentUserInfo(request)['user_id'])
    person.vname = request.POST.get("firstname")
    person.nname = request.POST.get("lastname")

    person.save()
    personProfile = None
    profileType = "client"
    if person.is_user == 1 and person.is_coach == 0:
        personProfile = ClientProfile.objects.filter(person_id=getCurrentUserInfo(request)['user_id']).first()
    if person.is_user == 0 and person.is_coach == 1:
        profileType = "coach"
        personProfile = CoachProfile.objects.filter(person_id=getCurrentUserInfo(request)['user_id']).first()


    profilePic = request.FILES.get("profilepic")

    image_path = None
    if profileType == "client":
        if personProfile:
            personProfileObj = ClientProfile.objects.get(id=personProfile.id)
            if profilePic:
                imagename = re.sub('[^A-Za-z0-9\.]+', '', profilePic.name)
                image_path = str(settings.BASE_DIR) + '/media/' + imagename
                try:
                    os.remove(os.path.join(settings.MEDIA_ROOT, personProfileObj.profile_pic))
                except:
                    pass
                personProfileObj.profile_pic = imagename
            personProfileObj.save()
        else:
            personProfileObj = ClientProfile(person_id=person)
            if profilePic:
                imagename = re.sub('[^A-Za-z0-9\.]+', '', profilePic.name)
                image_path = str(settings.BASE_DIR) + '/media/' + imagename
                personProfileObj.profile_pic = imagename
            personProfileObj.save()
    elif profileType == "coach":
        if personProfile:
            personProfileObj = CoachProfile.objects.get(id=personProfile.id)
            if profilePic:
                imagename = re.sub('[^A-Za-z0-9\.]+', '', profilePic.name)
                image_path = str(settings.BASE_DIR) + '/media/' + imagename
                try:
                    os.remove(os.path.join(settings.MEDIA_ROOT, personProfileObj.profile_pic))
                except:
                    pass
                personProfileObj.profile_pic = imagename
            personProfileObj.price = request.POST.get("price")
            personProfileObj.save()
        else:
            personProfileObj = CoachProfile(person_id=person)
            if profilePic:
                imagename = re.sub('[^A-Za-z0-9\.]+', '', profilePic.name)
                image_path = str(settings.BASE_DIR) + '/media/' + imagename
                personProfileObj.profile_pic = imagename
            personProfileObj.price = request.POST.get("price")
            personProfileObj.save()

    if image_path:
        with open(image_path, 'wb+') as f:
            for chunk in profilePic.chunks():
                f.write(chunk)


    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

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

    person = Person( vname=firstname,nname=lastname,email=email,pwd=password, is_user=is_user,is_coach=is_coach)
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
            seller = Person.objects.get(id=getCurrentUserInfo(request)['user_id'])
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
        price = None
        coachProfile = CoachProfile.objects.filter(person_id=person.id).first()
        if coachProfile:
            price = coachProfile.price;

        if price == None:
            return JsonResponse({'status': 'error'}, status=500)

        fee_percentage = 10 #person fee is 10 dollar
        appFee = (json_data['amount'] * 10)/100;
        try:
            customer = get_or_create_customer(
                getCurrentUserInfo(request)['email'],
                json_data['token'],
                person.stripe_access_token,
                person.stripe_user_id,
            )
            charge = stripe.Charge.create(
                amount=json_data['amount'],
                currency='usd',
                customer=customer.id,
                description=json_data['description'],
                application_fee=int(appFee),
                stripe_account=person.stripe_user_id,
            )
            if charge:
                chargeString = json.dumps(charge)
                client = Person.objects.get(id=getCurrentUserInfo(request)['user_id'])
                coach = Person.objects.get(id=person.id)
                stripePaymentDetail = StripePaymentDetail(client_id=client, coach_id=coach, payment_detail=chargeString)
                stripePaymentDetail.save()
                return JsonResponse({'status': 'success'}, status=200)
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
