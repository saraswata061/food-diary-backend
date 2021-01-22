import urllib
from rest_framework.decorators import api_view, permission_classes
from user.models import Person, PersonSymptome, PersonHandicap;
from user.models import StripePaymentDetail;
from django.http import JsonResponse
from user.models import ClientProfile;
from user.models import CoachProfile, CoachingRequest;
from user.models import UserChatHistory, FAQ, FAQAnswer;
from receipe.models import Lebensmittel, Handicap, Symptom
from receipe.views import getHandcapFoodSuggestion
from django.db.models import Q
from django.core.paginator import Paginator
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
from datetime import date
from datetime import datetime
from django.middleware.csrf import get_token




def csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})


@api_view(["POST"])
def deleteFAQ(request,faqid):
    faq = FAQ.objects.get(id=faqid)
    faqAnswer = FAQAnswer.objects.get(faq=faq)
    faqAnswer.delete()
    faq.delete()



    response = JsonResponse({}, safe=False);

    return response

@api_view(["GET"])
def getAllFAQ(request):
    faqs = FAQ.objects.all()
    pageno = request.GET.get('page', 1)
    paginator = Paginator(faqs, 5)
    faqs = paginator.page(pageno)

    fqResult = {}
    fqResult["pages"] = paginator.num_pages;
    fqResult["count"] = paginator.count;
    faqList = []

    for faq in faqs:
        faqAnswer = FAQAnswer.objects.get(faq=faq)
        faqDict = createFAQ(faq, faqAnswer)
        faqList.append(faqDict)
    fqResult["faqs"] = faqList;

    response = JsonResponse(fqResult, safe=False);

    return response

@api_view(["GET"])
def getFAQById(request, faqid):
    faq = FAQ.objects.get(id=faqid)
    faqAnswer = FAQAnswer.objects.get(faq=faq)
    faqObject =createFAQ(faq, faqAnswer)


    response = JsonResponse(faqObject, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


def createFAQ(faq,faqAnswer):
    faqObject = {
        "question": faq.question,
        "private": faq.private,
        "answer": faqAnswer.answer,
        "id": faq.id
    }
    return faqObject;


@api_view(["POST"])
def saveFAQ(request):
    finaldata = {}
    requestdata = dict(request.POST)
    for index in requestdata:
        finaldata[index] = requestdata[index]

    if int(finaldata.get("id")[0]) != 0:
        faq = FAQ.objects.get(id=finaldata["id"][0])
        setattr(faq, "question", finaldata["question"][0])
        setattr(faq, "private", finaldata["private"][0])

        if finaldata.get('answer'):
            faqAnswer = FAQAnswer.objects.get(faq=faq)
            faqAnswer.answer = finaldata.get('answer')[0]
            faqAnswer.save()
        faq.save()

    else:
        faq = FAQ(
            question=finaldata["question"][0],
            private=finaldata["private"][0]
        )

        faq.save()



        if finaldata.get('answer'):
            faqAnswer = FAQAnswer(faq=faq,answer=finaldata.get('answer')[0])
            faqAnswer.save()


    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


def getCurrentUserInfo(request):
    userInfo = {}
    userInfo['email'] = request.session['email']
    userInfo['password'] = request.session['password']
    userInfo['user_id'] = request.session['user_id']
    userInfo['authenticated'] = request.session['authenticated']
    userInfo['role'] = request.session['role']
    return userInfo;


@api_view(["GET"])
def user(request,userid):
    personDict = generateUserInfo(userid)
    response = JsonResponse(personDict,safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["POST"])
def appendUserChat(request):
    chatMessage = request.POST.get("chat_message")
    personIdOne = request.POST.get("person_id_one")
    personIdTwo = request.POST.get("person_id_two") #currentuser
    today = date.today()
    todayDateTime = datetime.combine(date.today(), datetime.min.time())
    if personIdOne:
        personOne = Person.objects.get(id=int(personIdOne))
        personTwo = Person.objects.get(id=int(personIdTwo))

        chatObject = {}
        chatObject['user_id'] = personIdTwo;
        chatObject['message'] = chatMessage;

        messageList = []

        userChats = UserChatHistory.objects.filter(Q(date=today ,personIdOne=personOne, personIdTwo=personTwo) | Q(date=today ,personIdOne=personTwo, personIdTwo=personOne))
        userChatObject = None
        for userChat in userChats:
            userChatObject = userChat
            chatMessageJSON = userChat.chatMessages
            messageList = json.loads(chatMessageJSON)

        if(len(messageList) == 0):
            messageList.append(chatObject)
            messageListJSON = json.dumps(messageList)
            userHistory = UserChatHistory(date=today, personIdOne=personOne, personIdTwo=personTwo,
                                          chatMessages=messageListJSON,id=uuid.uuid1())
            userHistory.save()
        else:
            messageList.append(chatObject)
            messageListJSON = json.dumps(messageList)
            userObj = UserChatHistory.objects.get(id=userChatObject.id)
            setattr(userObj, "chatMessages", messageListJSON)
            userObj.save()







    response = JsonResponse({},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["GET"])
def searchUser(request):
    email = request.GET.get("email","")
    country = request.GET.get("country", "")
    description = request.GET.get("description", "")
    role = request.GET.get("role", "")
    users = []
    users = Person.objects.filter()
    if len(email):
        users = users.filter(email__contains=email)
    if len(description):
        users = users.filter(description__contains=description)
    if len(country) > 0:
        users = users.filter(Q(client_profile__land__contains=country) | Q(coach_profile__land__contains=country))


    userList = []
    userResult = {}

    for user in users:
        if role == 'coach':
            if user.is_coach == True:
                continue
        if role == 'client':
            if user.is_user == True:
                continue
        userDict = createPersonResult(user)
        userList.append(userDict)
    userResult["users"] = userList;
    userResult["count"] = len(userList);
    response = JsonResponse(userResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["POST"])
def getUserChatMessages(request):
    personIdOne = request.POST.get("person_id_one")
    personIdTwo = request.POST.get("person_id_two")  # currentuser
    dateString = request.POST.get("date")

    dateObj = None
    if dateString:
        dateString = dateString + " 00:00:00"
        dateObj = datetime.strptime(dateString, "%Y-%m-%d %H:%M:%S")
    else:
        dateObj = date.today()

    messageList = []
    if personIdOne:
        personOne = Person.objects.get(id=int(personIdOne))
        personTwo = Person.objects.get(id=int(personIdTwo))
        userChats = UserChatHistory.objects.filter(
            Q(date=dateObj, personIdOne=personOne, personIdTwo=personTwo) | Q(date=dateObj, personIdOne=personTwo,
                                                                            personIdTwo=personOne))

        for userChat in userChats:
            chatMessageJSON = userChat.chatMessages
            messageList = json.loads(chatMessageJSON)

        finalResp = {}
        finalResp['userdata'] = {
            personTwo.id: createPersonResult(personTwo),
            personOne.id: createPersonResult(personOne),
        }
        finalResp['messagelist'] = messageList


        response = JsonResponse(finalResp,safe=False);
        #response.set_cookie('fdiarysess', cookie)

        return response


def generateUserInfo(user_id):
    person = Person.objects.get(id=user_id)
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
    personDict["description"] = person.description;

    personDict["symptomList"] = []
    personDict["symptomNameList"] = []
    personSymptoms = PersonSymptome.objects.filter(personId=person)
    for personSymptom in personSymptoms:
        if personSymptom.symptomeId.id:
            personDict["symptomList"].append(personSymptom.symptomeId.id)
            personDict["symptomNameList"].append(personSymptom.symptomeId.namen)

    personDict["handicapList"] = []
    personDict["handicapNameList"] = []
    personDict["handicapGoodFoodList"] = []
    personDict["handicapBadFoodList"] = []
    personHandicaps = PersonHandicap.objects.filter(personId=person)
    for personHandicap in personHandicaps:
        if personHandicap.handicapId.id:
            personDict["handicapList"].append(personHandicap.handicapId.id)
            personDict["handicapNameList"].append(personHandicap.handicapId.namen)
            personDict["handicapGoodFoodList"] = personDict["handicapGoodFoodList"] + \
                                                 getHandcapFoodSuggestion(personHandicap.handicapId.id)['goodFoodList']
            personDict["handicapBadFoodList"] = personDict["handicapGoodFoodList"] + \
                                                getHandcapFoodSuggestion(personHandicap.handicapId.id)['badFoodList']

    if person.is_user == 1 and person.is_coach == 0 :
        personDict["role"] = "client";
        personProfile = ClientProfile.objects.filter(person_id=user_id).first()
        if personProfile:
            personDict["profilepic"] = personProfile.profile_pic;
            personDict["mobno"] = personProfile.telefon;
            personDict["height"] = personProfile.groesse;
            personDict["weight"] = personProfile.gewicht;
            personDict["zipcode"] = personProfile.plz;
            personDict["country"] = personProfile.land;
            personDict["region"] = personProfile.ort;
            personDict["gender"] = personProfile.gender;
            personDict["smoke"] = bool(personProfile.smoking);
            personDict["pregnant"] = bool(personProfile.pregnant);
            personDict["breastfeeding"] = bool(personProfile.stillen);
            personDict["menopause"] = personProfile.menopause;
            personDict["pregnant"] = personProfile.pregnant;
            personDict["jobactivity"] = personProfile.job_activity;
            personDict["sportingactivity"] = personProfile.sport_activity;
            personDict["bday"] = personProfile.bday

    elif (person.is_user == 0 or person.is_user == 1)  and person.is_coach == 1:
        personDict["role"] = "coach";
        coachProfile = CoachProfile.objects.filter(person_id=user_id).first()
        if coachProfile:
            personDict["profilepic"] = coachProfile.profile_pic;
            personDict["price"] = coachProfile.price;
            personDict["country"] = coachProfile.land;
            personDict["region"] = coachProfile.ort;
            personDict["bday"] = coachProfile.bday
    return personDict


@api_view(["GET"])
def getCurrentUer(request):
    
    personDict = generateUserInfo(getCurrentUserInfo(request)['user_id'])
    response = JsonResponse(personDict,safe=False);
        #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getAllUser(request):
    persons = Person.objects.filter()
    page = request.GET.get('page', "")
    personResult = {}
    personlList = []
    currentUserRole = getCurrentUserInfo(request)['role']
    currentUserId = getCurrentUserInfo(request)['user_id']
    currentUser = Person.objects.get(id=currentUserId)
    allowedMsgToUser = []
    coachingRequests = CoachingRequest.objects.filter()

    if (currentUserRole == "admin"):
        persons = Person.objects.all()

    if (currentUserRole == "coach"):
        clientIdList = []
        #rezeptes = rezeptes.filter(rezepte_symptom__symptomeId__in=symptomList)
        coachingRequests = coachingRequests.filter(personIdCoach=currentUser)

        if page == "chatroom":
            coachingRequests = coachingRequests.filter(paymentStatus=True, requestStatus=1)
            for coachingRequest in coachingRequests:
                clientIdList.append(coachingRequest.personIdClient.id)
            persons = persons.filter(id__in=clientIdList)
        else:
            for coachingRequest in coachingRequests:
                clientIdList.append(coachingRequest.personIdClient.id)
            persons = persons.filter(id__in=clientIdList)

            coachingRequests = coachingRequests.filter(paymentStatus=True, requestStatus=1)
        for coachingRequest in coachingRequests:
            allowedMsgToUser.append(coachingRequest.personIdClient.id)


    if (currentUserRole == "client"):
        coachIdList = []

        if page == "chatroom":
            coachingRequests = coachingRequests.filter(personIdClient=currentUser)
            coachingRequests = coachingRequests.filter(paymentStatus=True, requestStatus=1)
            for coachingRequest in coachingRequests:
                coachIdList.append(coachingRequest.personIdCoach.id)
            persons = persons.filter(id__in=coachIdList)
        else:
            persons = persons.filter(is_user = False, is_coach = True)
            coachingRequests = coachingRequests.filter(personIdClient=currentUser)
            coachingRequests = coachingRequests.filter(paymentStatus=True, requestStatus=1)
            for coachingRequest in coachingRequests:
                allowedMsgToUser.append(coachingRequest.personIdCoach.id)


    for person in persons:
        personDict = createPersonResult(person)

        personlList.append(personDict)

    personResult["result"] = personlList;
    personResult['allowedMsgToUser'] = allowedMsgToUser


    response = JsonResponse(personResult,safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response



def createPersonResult(person):
    personDict = {};
    personDict["email"] = person.email;
    personDict["id"] = person.id;
    personDict["password"] = person.pwd;
    personDict["is_user"] = person.is_user;
    personDict["is_coach"] = person.is_coach;
    personDict["vname"] = person.vname;
    personDict["nname"] = person.nname;
    personDict["description"] = person.description;

    if person.is_user == 1 and person.is_coach == 0:
        personDict["role"] = "client"
        personProfile = ClientProfile.objects.filter(person_id=person.id).first()
        if personProfile:
            personDict["profilepic"] = personProfile.profile_pic;
    elif person.is_user == 0 and person.is_coach == 1:
        personDict["role"] = "coach"
        coachProfile = CoachProfile.objects.filter(person_id=person.id).first()
        if coachProfile:
            personDict["profilepic"] = coachProfile.profile_pic;
            personDict["price"] = coachProfile.price;
    elif person.is_user == 1 and person.is_coach == 1:
        personDict["role"] = "admin"

    return personDict

@api_view(["GET"])
def searchPerson(request):
    email = request.GET.get("email","")

    persons = None
    persons = Person.objects.filter()
    if len(email):
        persons = persons.filter(email__contains=email)

    personlList = []
    personResult = {}

    for person in persons:
        personDict = createPersonResult(person)
        personlList.append(personDict)
    personResult["persons"] = personlList;
    personResult["count"] = len(personlList);
    response = JsonResponse(personResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response




@api_view(["GET"])
def deleteUser(request,userid):
    person = Person.objects.get(id=userid)
    person.delete()

    response = JsonResponse({"succeess": True},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getCoachingRequests(request,coachid,clientid):
    personCoach = Person.objects.get(id=coachid)
    personClient = Person.objects.get(id=clientid)
    cocahingRequests = CoachingRequest.objects.filter(personIdCoach=personCoach, personIdClient=personClient)

    requeststatus = request.GET.get('requeststatus', '0')
    paymentstatus = request.GET.get('paymentstatus', '0')

    if(paymentstatus == '1'):
        cocahingRequests = cocahingRequests.filter(paymentStatus = False)

    if (paymentstatus == '2'):
        cocahingRequests = cocahingRequests.filter(paymentStatus=True)


    cocahingRequests = cocahingRequests.filter(requestStatus = requeststatus)

    pageno = request.GET.get('page', 1)
    paginator = Paginator(cocahingRequests, 5)
    cocahingRequests = paginator.page(pageno)

    coachResult = {}
    coachResult["pages"] = paginator.num_pages;
    coachResult["count"] = paginator.count;

    coachRequestList  = []
    for cocahingRequest in cocahingRequests:
        coachingDict = createCoachingReqObj(cocahingRequest)
        coachRequestList.append(coachingDict)

    coachResult["coachingReqList"] = coachRequestList
    response = JsonResponse(coachResult, safe=False);
    return response

@api_view(["GET"])
def getCoachingRequestsById(request,requestid):
    cocahingRequests = CoachingRequest.objects.get(id=requestid)



    coachingDict = createCoachingReqObj(cocahingRequests)
    response = JsonResponse(coachingDict, safe=False);
    return response




def createCoachingReqObj(cocahingRequest):
    coachReqDict = {}
    coachReqDict['title'] = cocahingRequest.title
    coachReqDict['description'] = cocahingRequest.description
    coachReqDict['requestcost'] = cocahingRequest.requestCost
    coachReqDict['feedbackcoach'] = cocahingRequest.feedbackCoach
    coachReqDict['ratingcoach'] = cocahingRequest.ratingCoach
    coachReqDict['feedbackclient'] = cocahingRequest.feedbackClient
    coachReqDict['ratingclient'] = cocahingRequest.ratingClient
    coachReqDict['requestStatus'] = cocahingRequest.requestStatus
    coachReqDict['paymentStatus'] = cocahingRequest.paymentStatus
    coachReqDict['comments'] = json.loads(cocahingRequest.comments)
    coachReqDict['id'] = cocahingRequest.id

    return coachReqDict
@api_view(["POST"])
def coachingRequest(request):
    finaldata = {}
    requestdata = dict(request.POST)
    for index in requestdata:
        finaldata[index] = requestdata[index]

    personIdCoach = request.POST.get("person_id_coach")
    personIdClient = request.POST.get("person_id_client")

    if  finaldata.get("requestcost"):
        try:
            value = float( finaldata["requestcost"][0])
        except ValueError:
            return JsonResponse({"messageList": ["Request cost can only be integer or float"]}, safe=False,
                                                status=500);



    if int(finaldata.get("id")[0]) != 0:
        coachingRequest = CoachingRequest.objects.get(id=finaldata["id"][0])
        setattr(coachingRequest, "title", finaldata["title"][0])
        setattr(coachingRequest, "description", finaldata["description"][0])
        setattr(coachingRequest, "comments", finaldata["comments"][0])
        setattr(coachingRequest, "requestCost", finaldata["requestcost"][0])
        setattr(coachingRequest, "feedbackCoach", finaldata["feedbackcoach"][0])
        setattr(coachingRequest, "ratingCoach", finaldata["ratingcoach"][0])
        setattr(coachingRequest, "feedbackClient", finaldata["feedbackclient"][0])
        setattr(coachingRequest, "ratingClient", finaldata["ratingclient"][0])
        setattr(coachingRequest, "requestStatus", finaldata["requestStatus"][0])

    else:
        personCoach = None
        personClient = None
        if personIdCoach:
            personCoach = Person.objects.get(id=int(personIdCoach))
        if personIdClient:
            personClient = Person.objects.get(id=int(personIdClient))

        coachingRequest = CoachingRequest(
            personIdCoach=personCoach,
            personIdClient=personClient,
            title=finaldata["title"][0],
            description=finaldata["description"][0],
            comments=finaldata["comments"][0],
            requestCost=finaldata["requestcost"][0],
            feedbackCoach=finaldata["feedbackcoach"][0],
            ratingCoach=finaldata["ratingcoach"][0],
            feedbackClient=finaldata["feedbackclient"][0],
            ratingClient=finaldata["ratingclient"][0],
            requestStatus=finaldata["requestStatus"][0]
        )

    coachingRequest.save()

    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["POST"])
def updateUserProfile(request):
    person = Person.objects.get(id=getCurrentUserInfo(request)['user_id'])
    person.vname = request.POST.get("firstname")
    person.nname = request.POST.get("lastname")
    finaldata = {}
    finaldata["symptoms"] = []
    finaldata["allergies"] = []
    requestdata = dict(request.POST)
    for index in requestdata:
        indexsplit = index.split("|")
        if len(indexsplit) > 1:
            if indexsplit[0] == "symptoms":
                finaldata["symptoms"].append(requestdata["symptoms" + "|" + indexsplit[1]][0])
            if indexsplit[0] == "allergies":
                finaldata["allergies"].append(requestdata["allergies" + "|" + indexsplit[1]][0])
        else:
            finaldata[index] = requestdata[index]

    person.save()
    personProfile = None
    profileType = "coach"
    if person.is_user == 1 and person.is_coach == 0:
        personProfile = ClientProfile.objects.filter(person_id=getCurrentUserInfo(request)['user_id']).first()
        profileType = "client"
    if person.is_user == 0 and person.is_coach == 1:
        profileType = "coach"
        personProfile = CoachProfile.objects.filter(person_id=getCurrentUserInfo(request)['user_id']).first()


    profilePic = request.FILES.get("profilepic")

    image_path = None


    if profileType == "client":

        if finaldata.get('zipcode'):
            if finaldata['zipcode'][0] == 'undefined':
                return JsonResponse({"messageList": ["Zip Code is required"]}, safe=False, status=500);

        if finaldata.get('mobno'):
            if finaldata['mobno'][0] == 'undefined':
                return JsonResponse({"messageList": ["Mobile Number is required"]}, safe=False, status=500);
            try:
                value = float(finaldata.get('weight')[0])
            except ValueError:
                return JsonResponse({"messageList": ["Mobile Number can only be integer or float"]}, safe=False, status=500);

        if finaldata.get('height'):
            if finaldata['height'][0] == 'undefined':
                return JsonResponse({"messageList": ["Height is required"]}, safe=False, status=500);
            try:
                value = int(finaldata.get('height')[0])
            except ValueError:
                return JsonResponse({"messageList": ["Height can only be integer"]}, safe=False, status=500);

        if finaldata.get('weight'):
            if finaldata['weight'][0] == 'undefined':
                return JsonResponse({"messageList": ["Weight is required"]}, safe=False, status=500);
            try:
                value = float(finaldata.get('weight')[0])
            except ValueError:
                return JsonResponse({"messageList": ["Weight can only be integer or float"]}, safe=False, status=500);




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
            #personProfileObj.save()
        else:
            personProfileObj = ClientProfile(person_id=person)
            if profilePic:
                imagename = re.sub('[^A-Za-z0-9\.]+', '', profilePic.name)
                image_path = str(settings.BASE_DIR) + '/media/' + imagename
                personProfileObj.profile_pic = imagename
            personProfileObj.save()
        if finaldata.get('symptoms'):
            if len(finaldata.get('symptoms')) > 0:
                personSymptoms = PersonSymptome.objects.filter(personId=person)
                PersonSymptome.objects.filter(personId=person).delete()
                for key in finaldata["symptoms"]:
                    if key != "undefined":
                        symptom = Symptom.objects.get(id=int(key))
                        personSymptom = PersonSymptome(personId=person, symptomeId=symptom)
                        personSymptom.save()

        if finaldata.get('allergies'):
            if len(finaldata.get('allergies')) > 0:
                rezepteHandicaps = PersonHandicap.objects.filter(personId=person)
                PersonHandicap.objects.filter(personId=person).delete()
                for key in finaldata["allergies"]:
                    if key != "undefined":
                        handicap = Handicap.objects.get(id=int(key))
                        personHandicap = PersonHandicap(personId=person, handicapId=handicap)
                        personHandicap.save()


        if finaldata.get('zipcode'):
            personProfileObj.plz = finaldata['zipcode'][0]
        if finaldata.get('mobno'):
            if finaldata['mobno'][0] == 'undefined':
                return JsonResponse({"messageList": ["Mobile Number is required"]}, safe=False, status=500);
            try:
                value = float(finaldata.get('weight')[0])
            except ValueError:
                return JsonResponse({"messageList": ["Mobile Number can only be integer or float"]}, safe=False, status=500);
            personProfileObj.telefon = finaldata['mobno'][0]
        if finaldata.get('height'):
            if finaldata['height'][0] == 'undefined':
                return JsonResponse({"messageList": ["Height is required"]}, safe=False, status=500);
            personProfileObj.groesse = finaldata['height'][0]
        if finaldata.get('weight'):
            if finaldata['weight'][0] == 'undefined':
                return JsonResponse({"messageList": ["Weight is required"]}, safe=False, status=500);
            personProfileObj.groesse = finaldata['height'][0]
            personProfileObj.gewicht = finaldata['weight'][0]
        if finaldata.get('country'):
            personProfileObj.land = finaldata['country'][0]
        if finaldata.get('region'):
            personProfileObj.ort = finaldata['region'][0]
        if finaldata.get('gender'):
            personProfileObj.gender = finaldata['gender'][0]
        if finaldata.get('smoke'):
            personProfileObj.smoking = True if (finaldata['smoke'][0] == "true") else False
        if finaldata.get('pregnant'):
            personProfileObj.pregnant = True if (finaldata['pregnant'][0] == "true") else False
        if finaldata.get('jobactivity'):
            personProfileObj.job_activity = finaldata['jobactivity'][0]
        if finaldata.get('sportingactivity'):
            personProfileObj.sport_activity = finaldata['sportingactivity'][0]
        if finaldata.get('breastfeeding'):
            personProfileObj.stillen =  True if (finaldata['breastfeeding'][0] == "true") else False
        if finaldata.get('bday'):
            personProfileObj.bday = finaldata['bday'][0]
        personProfileObj.save()

    elif profileType == "coach":
        if finaldata.get('price'):
            try:
                value = int(finaldata.get('price')[0])
            except ValueError:
                return JsonResponse({"messageList": ["Price must be integer"]}, safe=False, status=500);
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
        if finaldata.get('country'):
            personProfileObj.land = finaldata['country'][0]
        if finaldata.get('region'):
            personProfileObj.ort = finaldata['region'][0]
        if finaldata.get('bday'):
            personProfileObj.bday = finaldata['bday'][0]

        personProfileObj.save()
    if finaldata.get('description'):
        person.description = finaldata['description'][0]

    person.save()
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
    id = request.data['userid']
    lastname = request.data['lastname']
    email = request.data['email']
    password = ""
    if request.data['password'].encode('utf-8').strip() != "":
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
    if id == 0:
        person = Person( vname=firstname,nname=lastname,email=email,pwd=password, is_user=is_user,is_coach=is_coach)
        person.save()
    else:
        person = Person.objects.get(id=id)
        if firstname.strip() != "":
            setattr(person, "vname", firstname)
        if lastname.strip() != "":
            setattr(person, "nname", lastname)
        if email.strip() != "":
            setattr(person, "email", email)
        if password.strip() != "":
            setattr(person, "pwd", password)
        setattr(person, "is_user", is_user)
        setattr(person, "is_coach", is_coach)

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

        fee_percentage = 20 #app fee is 20%
        appFee = (json_data['amount'] * fee_percentage)/100;
        payment_type = json_data['payment_type']

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
                if payment_type == "coaching":
                    coachingReq =  CoachingRequest.objects.get(id=json_data['coachrequestid'])
                    stripePaymentDetail = StripePaymentDetail(client_id=client, coach_id=coach, payment_detail=chargeString, payment_type = payment_type, coaching_id=coachingReq)
                    stripePaymentDetail.save()
                    setattr(coachingReq, "paymentStatus", True)
                    coachingReq.save()
                return JsonResponse({'status': 'success'}, status=200)
        except stripe.error.StripeError as e:
            return JsonResponse({"messageList": ["Payment Failed"]}, safe=False, status=500);

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
