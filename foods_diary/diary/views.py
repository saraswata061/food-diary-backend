from django.shortcuts import render

from rest_framework.decorators import api_view
from diary.models import Mahlzeiten, Emotion, Buch, BuchLebensmittel;
from django.http import JsonResponse
from user.models import Person;
from receipe.models import Lebensmittel;
from user.views import getCurrentUserInfo;
import time;
import os
import re
from django.conf import settings
from django.core.paginator import Paginator

@api_view(["POST"])
def createDiary(request):
    finaldata = {}
    requestdata = dict(request.POST)
    for index in requestdata:
        indexsplit = index.split("|")
        if len(indexsplit) > 1:
            if indexsplit[0] == "food":
                if finaldata.get("food") is None:
                    finaldata["food"] = {}
                if  finaldata["food"].get(indexsplit[1]) is None:
                    finaldata["food"][indexsplit[1]] = {}
                finaldata["food"][indexsplit[1]][indexsplit[2]] = requestdata["food"+"|"+indexsplit[1]+"|"+indexsplit[2]]
        else:
            finaldata[index] = requestdata[index]

        #First create receipe
    person = Person.objects.get(id=getCurrentUserInfo(request)['user_id']);
    mahlzeiten = Mahlzeiten.objects.get(id=finaldata["meal"][0]);
    emotion = Emotion.objects.get(id=finaldata["emotion"][0]);
    buch = Buch(person_id=person, mahlzeiten_id=mahlzeiten,emotion_id=emotion,uhrzeit=finaldata["uhrzeit"][0],updated=time.time())
    buch.save()

    for key in finaldata["food"]:
        imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
        imagename = str(buch.id)+imagename
        lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
        buchLebensmittel = BuchLebensmittel(buchId=buch, lebensmittelId=lebensmittel,menge=finaldata["food"][key]['quantity'][0],bild_link=imagename)
        buchLebensmittel.save()

    for fileIndex in request.FILES:
        img = request.FILES[fileIndex]
        img_extension = os.path.splitext(img.name)[1]
        imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)
        imagename = str(buch.id) + imagename
        food_folder = str(settings.BASE_DIR) + '/media/' + imagename

        with open(food_folder, 'wb+') as f:
            for chunk in img.chunks():
                f.write(chunk)

    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["POST"])
def updateDiary(request, buchid):
    finaldata = {}
    requestdata = dict(request.POST)
    for index in requestdata:
        indexsplit = index.split("|")
        if len(indexsplit) > 1:
            if indexsplit[0] == "food":
                if finaldata.get("food") is None:
                    finaldata["food"] = {}
                if  finaldata["food"].get(indexsplit[1]) is None:
                    finaldata["food"][indexsplit[1]] = {}
                finaldata["food"][indexsplit[1]][indexsplit[2]] = requestdata["food"+"|"+indexsplit[1]+"|"+indexsplit[2]]
        else:
            finaldata[index] = requestdata[index]

    buch = Buch.objects.get(id=buchid);
    mahlzeiten = Mahlzeiten.objects.get(id=finaldata["meal"][0]);
    emotion = Emotion.objects.get(id=finaldata["emotion"][0]);
    setattr(buch, "mahlzeiten_id",mahlzeiten )
    setattr(buch, "emotion_id", emotion)
    setattr(buch, "time", finaldata["uhrzeit"][0])
    setattr(buch, "updated", time.time())

    buch.save()

    buchLebensmittels = BuchLebensmittel.objects.filter(buchId=buch)
    for buchLebensmittel in buchLebensmittels:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, buchLebensmittel.bild_link))
        except:
            pass
    BuchLebensmittel.objects.filter(buchId=buch).delete()


    if finaldata.get("food"):
        for key in finaldata["food"]:
            imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
            imagename = str(buch.id) + imagename
            lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
            buchLebensmittel = BuchLebensmittel(buchId=buch, lebensmittelId=lebensmittel,menge=finaldata["food"][key]['quantity'][0],bild_link=imagename)
            buchLebensmittel.save()




        for fileIndex in request.FILES:
            img = request.FILES[fileIndex]
            img_extension = os.path.splitext(img.name)[1]
            imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)
            imagename = str(buch.id) + imagename
            food_folder = str(settings.BASE_DIR)+'/media/'+imagename

            with open(food_folder, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)



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
    buchs = Buch.objects.all()
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


def createBuchResponseFromBuchObject(buch):
    buchDict = {}
    buchDict["id"] = buch.id
    buchDict["meal"] = buch.mahlzeiten_id.mahlzeit
    buchDict["meal_id"] = buch.mahlzeiten_id.id
    buchDict["emotion"] = buch.emotion_id.namen
    buchDict["emotion_id"] = buch.emotion_id.id
    buchDict["time"] = buch.updated
    buchDict["uhrzeit"] = buch.uhrzeit
    buchDictFoodList = []
    buchLebensmittels = BuchLebensmittel.objects.filter(buchId=buch)
    for buchLebensmittel in buchLebensmittels:
        buchFoodDict = {}
        buchFoodDict["buchLebensmitteId"] = buchLebensmittel.lebensmittelId.id
        buchFoodDict["buchLebensmitteName"] = buchLebensmittel.lebensmittelId.name
        buchFoodDict["bild_link"] = buchLebensmittel.bild_link
        buchFoodDict["menge"] = buchLebensmittel.menge
        buchDictFoodList.append(buchFoodDict)
    buchDict["buchDictFoodList"] = buchDictFoodList
    return buchDict


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

    buch.delete()

    response = JsonResponse({}, safe=False);

    return  response

