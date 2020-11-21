from datetime import datetime

from django.shortcuts import render

from rest_framework.decorators import api_view
from diary.models import Mahlzeiten, Emotion, Buch, BuchLebensmittel, BuchSymptome;
from django.http import JsonResponse
from user.models import Person;
from receipe.models import Lebensmittel, Symptom;
from user.views import getCurrentUserInfo, generateUserInfo;
from receipe.views import createLebensmittel;
import time;
import os
import re
from django.conf import settings
from django.core.paginator import Paginator
import datetime
from django.db.models import Q
import json


def getCurrentUserInfo(request):
    userInfo = {}
    userInfo['email'] = request.session['email']
    userInfo['password'] = request.session['password']
    userInfo['user_id'] = request.session['user_id']
    userInfo['authenticated'] = request.session['authenticated']
    userInfo['role'] = request.session['role']
    return userInfo;

@api_view(["POST"])
def createDiary(request):
    errorMessageList = []
    finaldata = {}
    requestdata = dict(request.POST)
    if request.POST.get("type") == "symptom":
        finaldata["symptoms"] = []
        for index in requestdata:
            indexsplit = index.split("|")
            if len(indexsplit) > 1:
                if indexsplit[0] == "symptoms":
                    finaldata["symptoms"].append(requestdata["symptoms" + "|" + indexsplit[1]][0])
            else:
                finaldata[index] = requestdata[index]

        if not finaldata.get("symptoms"):
            return JsonResponse({"messageList": ["Symptom list can not be empty"]}, safe=False, status=500);

        person = Person.objects.get(id=getCurrentUserInfo(request)['user_id']);
        buch = Buch(person_id=person, uhrzeit=finaldata["uhrzeit"][0],updated=time.time(),buch_type="symptome",author=getCurrentUserInfo(request)['user_id'])
        buch.save()

        if finaldata.get('symptoms'):
            if len(finaldata.get('symptoms')) > 0:
                diarySymptoms = BuchSymptome.objects.filter(buchId=buch)
                BuchSymptome.objects.filter(buchId=buch).delete()
                for key in finaldata["symptoms"]:
                    symptom = Symptom.objects.get(id=int(key))
                    buchSymptom = BuchSymptome(buchId=buch, symptomeId=symptom)
                    buchSymptom.save()
    else:
        for index in requestdata:
            indexsplit = index.split("|")
            if len(indexsplit) > 1:
                if indexsplit[0] == "food":
                    if finaldata.get("food") is None:
                        finaldata["food"] = {}
                    if  finaldata["food"].get(indexsplit[1]) is None:
                        finaldata["food"][indexsplit[1]] = {}
                    if indexsplit[2] == "selectedFood":
                        continue
                    finaldata["food"][indexsplit[1]][indexsplit[2]] = requestdata["food"+"|"+indexsplit[1]+"|"+indexsplit[2]]
            else:
                finaldata[index] = requestdata[index]

        if not finaldata.get("food"):
            return JsonResponse({"messageList":["Food list can not be empty"]}, safe=False, status=500);

        if not finaldata.get("meal"):
            return JsonResponse({"messageList": ["Select meal is a required field"]}, safe=False, status=500);

        if not finaldata.get("emotion"):
            return JsonResponse({"messageList": ["Select emotion is a required field"]}, safe=False, status=500);

        if finaldata["emotion"][0] == "_none":
            return JsonResponse({"messageList": ["Select emotion is a required field"]}, safe=False, status=500);

        if finaldata["meal"][0] == "_none":
            return JsonResponse({"messageList": ["Select meal is a required field"]}, safe=False, status=500);

        foodlist = []
        if finaldata.get('food'):
            for key in finaldata["food"]:
                if not finaldata["food"][key].get('food'):
                    return JsonResponse({"messageList": ["Lebensmittel is a required field"]}, safe=False, status=500);
                elif not finaldata["food"][key].get('quantity'):
                    return JsonResponse({"messageList": ["Quantity is a required field"]}, safe=False, status=500);
                else:
                    if finaldata.get('quantity'):
                        try:
                            value = float(finaldata.get('quantity')[0])
                        except ValueError:
                            return JsonResponse({"messageList": ["Quantity can only be integer or float"]}, safe=False,
                                                status=500);
                    if finaldata["food"][key].get('food')[0] in foodlist:
                        return JsonResponse({"messageList": ["Same lebensmittel can not be used twice"]}, safe=False,
                                            status=500);
                    foodlist.append(finaldata["food"][key].get('food')[0])


        person = Person.objects.get(id=getCurrentUserInfo(request)['user_id']);

        mahlzeiten = Mahlzeiten.objects.get(id=finaldata["meal"][0]);
        emotion = Emotion.objects.get(id=finaldata["emotion"][0]);
        buch = Buch(person_id=person, mahlzeiten_id=mahlzeiten,emotion_id=emotion,uhrzeit=finaldata["uhrzeit"][0],updated=time.time(),author=getCurrentUserInfo(request)['user_id'])
        buch.save()

        updateDiaryFoodList(finaldata, request, buch)

    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


def calculateFood(lebensmittel, quantity):
    quantity = float(quantity)
    lebensmittelDet = createLebensmittel(lebensmittel)

    foodNutrition = {}

    #for 100 gm or 100ml
    foodCalories = lebensmittelDet.get('calories')
    foodKilojoule = lebensmittelDet.get('kilojoule')
    foodBreadunit = lebensmittelDet.get('breadunit')
    foodCarbohydrates = lebensmittelDet.get('carbohydrates')
    foodBold = lebensmittelDet.get('bold')
    foodProtein = lebensmittelDet.get('protein')
    foodCsalary = lebensmittelDet.get('csalary')

    #for provided quantity
    foodNutrition['calories']  = round((foodCalories/100) * quantity,2)
    foodNutrition['kilojoule'] = round((foodKilojoule / 100) * quantity, 2)
    foodNutrition['breadunit'] = round((foodBreadunit / 100) * quantity, 2)
    foodNutrition['carbohydrates'] = round((foodCarbohydrates / 100) * quantity, 2)
    foodNutrition['bold'] = round((foodBold / 100) * quantity, 2)
    foodNutrition['protein'] = round((foodProtein / 100) * quantity, 2)
    foodNutrition['csalary'] = round((foodCsalary / 100) * quantity, 2)

    foodNutrition = json.dumps(foodNutrition)

    return foodNutrition



def updateDiaryFoodList(finaldata, request, entity):
    for key in finaldata["food"]:
        imagename = ""
        quantity = "";
        lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))


        foodNutrition = None

        if finaldata["food"][key].get('quantity'):
            measure = "gm";
            if finaldata["food"][key].get('measure'):
                measure = finaldata["food"][key]['measure'][0]
            quantity = finaldata["food"][key]['quantity'][0]+" "+measure
            foodNutrition = calculateFood(lebensmittel, finaldata["food"][key]['quantity'][0])
        if finaldata["food"][key].get('food_image_name'):
            imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
            imagename = str(entity.id) + imagename

        buchLebensmittel = BuchLebensmittel(buchId=entity, lebensmittelId=lebensmittel, menge=quantity,
                                            bild_link=imagename, nutrition= foodNutrition)
        buchLebensmittel.save()
        if request.FILES.get("food|" + key + "|food_image_file"):
            img = request.FILES["food|" + key + "|food_image_file"]
            img_extension = os.path.splitext(img.name)[1]
            imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)
            imagename = str(entity.id) + imagename
            food_folder = str(settings.BASE_DIR) + '/media/' + imagename

            with open(food_folder, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)




@api_view(["POST"])
def updateDiary(request, buchid):
    finaldata = {}
    requestdata = dict(request.POST)
    finaldata["symptoms"] = []
    if request.POST.get("type") == "symptom":
        for index in requestdata:
            indexsplit = index.split("|")
            if len(indexsplit) > 1:
                if indexsplit[0] == "symptoms":
                    finaldata["symptoms"].append(requestdata["symptoms" + "|" + indexsplit[1]][0])
            else:
                finaldata[index] = requestdata[index]
        if not finaldata.get("symptoms"):
            return JsonResponse({"messageList": ["Symptom list can not be empty"]}, safe=False, status=500);
        buch = Buch.objects.get(id=buchid);
        setattr(buch, "uhrzeit", finaldata["uhrzeit"][0])
        setattr(buch, "updated", time.time())

        buch.save()

        if len(finaldata.get('symptoms')) > 0:
            buchSymptoms = BuchSymptome.objects.filter(buchId=buch)
            BuchSymptome.objects.filter(buchId=buch).delete()
            for key in finaldata["symptoms"]:
                symptom = Symptom.objects.get(id=int(key))
                buchSymptom = BuchSymptome(buchId=buch, symptomeId=symptom)
                buchSymptom.save()
    else:
        for index in requestdata:
            indexsplit = index.split("|")
            if len(indexsplit) > 1:
                if indexsplit[0] == "food":
                    if finaldata.get("food") is None:
                        finaldata["food"] = {}
                    if  finaldata["food"].get(indexsplit[1]) is None:
                        finaldata["food"][indexsplit[1]] = {}
                    if indexsplit[2] == "selectedFood":
                        continue
                    finaldata["food"][indexsplit[1]][indexsplit[2]] = requestdata["food"+"|"+indexsplit[1]+"|"+indexsplit[2]]
            else:
                finaldata[index] = requestdata[index]

        if not finaldata.get("food"):
            return JsonResponse({"messageList":["Food list can not be empty"]}, safe=False, status=500);

        if not finaldata.get("meal"):
            return JsonResponse({"messageList": ["Select meal is a required field"]}, safe=False, status=500);

        if not finaldata.get("emotion"):
            return JsonResponse({"messageList": ["Select emotion is a required field"]}, safe=False, status=500);

        if finaldata["emotion"][0] == "_none":
            return JsonResponse({"messageList": ["Select emotion is a required field"]}, safe=False, status=500);

        if finaldata["meal"][0] == "_none":
            return JsonResponse({"messageList": ["Select meal is a required field"]}, safe=False, status=500);
        foodlist = []
        if finaldata.get('food'):
            for key in finaldata["food"]:
                if not finaldata["food"][key].get('food'):
                    return JsonResponse({"messageList": ["Lebensmittel is a required field"]}, safe=False, status=500);
                elif not finaldata["food"][key].get('quantity'):
                    return JsonResponse({"messageList": ["Quantity is a required field"]}, safe=False, status=500);
                else:
                    if finaldata["food"][key].get('quantity'):
                        try:
                            value = float(finaldata["food"][key].get('quantity')[0])
                        except ValueError:
                            return JsonResponse({"messageList": ["Quantity can only be integer or float"]}, safe=False,
                                                status=500);
                    if finaldata["food"][key].get('food')[0] in foodlist:
                        return JsonResponse({"messageList": ["Same lebensmittel can not be used twice"]}, safe=False,
                                            status=500);
                    foodlist.append(finaldata["food"][key].get('food')[0])



        buch = Buch.objects.get(id=buchid);
        mahlzeiten = Mahlzeiten.objects.get(id=finaldata["meal"][0]);
        emotion = Emotion.objects.get(id=finaldata["emotion"][0]);
        setattr(buch, "mahlzeiten_id",mahlzeiten )
        setattr(buch, "emotion_id", emotion)
        setattr(buch, "uhrzeit", finaldata["uhrzeit"][0])
        setattr(buch, "updated", time.time())

        buch.save()

        buchLebensmittels = BuchLebensmittel.objects.filter(buchId=buch)
        for buchLebensmittel in buchLebensmittels:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, buchLebensmittel.bild_link))
            except:
                pass
        BuchLebensmittel.objects.filter(buchId=buch).delete()

        updateDiaryFoodList(finaldata, request, buch)

    response = JsonResponse({},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["GET"])
def getBuchById(request, buchid):
    buch = Buch.objects.get(id=buchid)
    buchDict = createBuchResponseFromBuchObject(buch)
    response = JsonResponse(buchDict, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getAllBuch(request):
    clinetid = request.GET.get('clientid', 1)
    buchs = None
    if getCurrentUserInfo(request)['role'] == 'admin':
        buchs = Buch.objects.all()
    elif getCurrentUserInfo(request)['role'] == 'client':
        buchs = Buch.objects.filter(author=getCurrentUserInfo(request)['user_id'])
    elif getCurrentUserInfo(request)['role'] == 'coach':
        buchs = Buch.objects.filter(author=clinetid)

    pageno = request.GET.get('page', 1)
    paginator = Paginator(buchs, 5)
    buchs = paginator.page(pageno)

    buchResult = {}
    buchResult["pages"] = paginator.num_pages;
    buchResult["count"] = paginator.count;
    buchlList = []

    for buch in buchs:
        bucheDict = createBuchResponseFromBuchObject(buch)
        buchlList.append(bucheDict)
    buchResult["buchs"] = buchlList;

    response = JsonResponse(buchResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response



@api_view(["GET"])
def searchDiary(request):
    lebensmittels = request.GET.get("lebensmittels", "")
    selecteddate = request.GET.get("selectedDate", "")
    endTime = request.GET.get("endTime", "")


    lebensmittelList = [Lebensmittel.objects.get(id=int(i)) for i in lebensmittels.split(',') if i.strip() != ""]

    rezeptes = None
    buchs = Buch.objects.filter()


    buchs = buchs.filter(author=getCurrentUserInfo(request)['user_id'])

    if len(lebensmittelList) > 0:
        buchs = buchs.filter(buch_lebensmittel__lebensmittelId__in=lebensmittelList)

    if selecteddate:
        selecteddateObj = datetime.datetime.strptime(selecteddate, "%Y-%m-%dT%H:%M:%S.%fZ")
        selectedenddateObj = datetime.datetime.strptime(endTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        buchs = buchs.filter(uhrzeit__gte=selecteddateObj)
        buchs = buchs.filter(uhrzeit__lte=selectedenddateObj)


    buchlList = []
    buchResult = {}

    for buch in buchs:
        rezepteDict = createBuchResponseFromBuchObject(buch)
        buchlList.append(rezepteDict)
    buchResult["buchs"] = buchlList;
    buchResult["count"] = len(buchlList);
    response = JsonResponse(buchResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

def createBuchResponseFromBuchObject(buch):
    buchDict = {}
    if buch:
        if buch.id:
            buchDict["id"] = buch.id
            buchDict["buchDictFoodList"] = []
            buchDict["buchDictSymptomList"] = []
            nutritionList = []
            if buch.buch_type != 'symptome':
                buchDict["meal"] = buch.mahlzeiten_id.mahlzeit
                buchDict["meal_id"] = buch.mahlzeiten_id.id
                buchDict["emotion"] = buch.emotion_id.namen
                buchDict["emotion_id"] = buch.emotion_id.id

                buchDictFoodList = []
                buchLebensmittels = BuchLebensmittel.objects.filter(buchId=buch)
                for buchLebensmittel in buchLebensmittels:
                    buchFoodDict = {}
                    buchFoodDict["buchLebensmitteId"] = buchLebensmittel.lebensmittelId.id
                    buchFoodDict["buchLebensmitteName"] = buchLebensmittel.lebensmittelId.name
                    buchFoodDict["bild_link"] = buchLebensmittel.bild_link
                    buchFoodDict["menge"] = buchLebensmittel.menge

                    if buchLebensmittel.nutrition:
                        buchFoodDict["nutrition"] = buchLebensmittel.nutrition
                        nutritionList.append(buchLebensmittel.nutrition)
                    else:
                        buchFoodDict["nutrition"] = "{}"

                    buchDictFoodList.append(buchFoodDict)
                buchDict["buchDictFoodList"] = buchDictFoodList
            else:
                buchDictSymptomList = []
                buchSymptoms = BuchSymptome.objects.filter(buchId=buch)
                buchSymptomNameList = []
                for buchSymptom in buchSymptoms:
                    buchSymptomDict = {}
                    buchSymptomDict["id"] = buchSymptom.symptomeId.id
                    buchSymptomNameList.append(buchSymptom.symptomeId.namen)
                    buchSymptomDict["name"] = buchSymptom.symptomeId.namen
                    buchDictSymptomList.append(buchSymptomDict)
                buchDict["buchDictSymptomList"] = buchDictSymptomList
                buchDict["buchSymptomNameList"] = buchSymptomNameList
            buchDict["time"] = buch.updated
            buchDict["type"] = buch.buch_type
            buchDict["uhrzeit"] = buch.uhrzeit
            buchDict["nutrition"] = sumNutrition(nutritionList)


    return buchDict


def sumNutrition(nutritionList):
    foodNutrition = {
        'calories' : 0,
        'kilojoule': 0,
        'breadunit': 0,
        'carbohydrates': 0,
        'bold': 0,
        'protein': 0,
        'csalary': 0
    }

    for nutrition in nutritionList:

        nutritionDict = json.loads(nutrition)

        # for provided quantity
        foodNutrition['calories'] = foodNutrition['calories'] + nutritionDict.get('calories')
        foodNutrition['kilojoule'] = foodNutrition['kilojoule'] +  nutritionDict.get('kilojoule')
        foodNutrition['breadunit'] = foodNutrition['breadunit'] + nutritionDict.get('breadunit')
        foodNutrition['carbohydrates'] = foodNutrition['carbohydrates'] + nutritionDict.get('carbohydrates')
        foodNutrition['bold'] = foodNutrition['bold'] + nutritionDict.get('bold')
        foodNutrition['protein'] = foodNutrition['protein'] + nutritionDict.get('protein')
        foodNutrition['csalary'] = foodNutrition['csalary'] + nutritionDict.get('csalary')

    return foodNutrition;




@api_view(["GET"])
def getMahlzeiten(request):
    mahlzeiten = Mahlzeiten.objects.all()

    mahlzeitenList = []

    for mahlzeitenobj in mahlzeiten:
        mahlzeitenDict = {}
        mahlzeitenDict["id"] = mahlzeitenobj.id
        mahlzeitenDict["name"] = mahlzeitenobj.mahlzeit
        mahlzeitenList.append(mahlzeitenDict)

    response = JsonResponse(mahlzeitenList, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getEmotion(request):
    emotions = Emotion.objects.all()

    emotionList = []

    for emotion in emotions:
        emotionDict = {}
        emotionDict["id"] = emotion.id
        emotionDict["name"] = emotion.namen
        emotionList.append(emotionDict)

    response = JsonResponse(emotionList, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["POST"])
def deleteBuch(request, buchid):
    buch = Buch.objects.get(id=buchid)


    buchLebensmittels = BuchLebensmittel.objects.filter(buchId=buch)
    for buchLebensmittel in buchLebensmittels:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, buchLebensmittel.bild_link))
        except:
            pass
    BuchLebensmittel.objects.filter(buchId=buch).delete()
    BuchSymptome.objects.filter(buchId=buch).delete()
    buch.delete()

    response = JsonResponse({}, safe=False);

    return  response

