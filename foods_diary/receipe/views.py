from django.shortcuts import render

from rest_framework.decorators import api_view
from django.http import JsonResponse
import uuid
import os
import re
from django.conf import settings
from receipe.models import Lebensmittel, Rezepte, RezepteLebensmittel, Handicap, Symptom, RezepteSymptome, RezepteHandicap;
from django.core.paginator import Paginator
import time



import json



@api_view(["POST"])
def createReceipe(request):
    finaldata = {}
    finaldata["symptoms"] = []
    finaldata["allergies"] = []
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
            if indexsplit[0] == "symptoms":
                finaldata["symptoms"].append(requestdata["symptoms" + "|" + indexsplit[1]][0])
            if indexsplit[0] == "allergies":
                finaldata["allergies"].append(requestdata["allergies" + "|" + indexsplit[1]][0])
        else:
            finaldata[index] = requestdata[index]

    #First create receipe
    buchlink = ""
    buchauthor = ""
    if finaldata.get("buchlink"):
        buchlink =   finaldata["buchlink"][0]
    if finaldata.get("buchauthor"):
        buchauthor=  finaldata["buchauthor"][0]
    rezepte = Rezepte(namen=finaldata["title"][0], beschreibung=finaldata["beschreibung"][0],updated=time.time(), buch_link=buchlink, buch_author=buchauthor)
    rezepte.save()
    if finaldata.get("food"):
        for key in finaldata["food"]:
            if finaldata["food"][key].get('food_image_name'):
                imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
                imagename = str(rezepte.id)+imagename
                lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
                rezepteLebensmittel = RezepteLebensmittel(rezepteId=rezepte, lebensmittelId=lebensmittel,menge=finaldata["food"][key]['quantity'][0],bild_link=imagename)
                rezepteLebensmittel.save()




        for fileIndex in request.FILES:
            img = request.FILES[fileIndex]
            img_extension = os.path.splitext(img.name)[1]
            imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)
            imagename = str(rezepte.id) + imagename
            food_folder = str(settings.BASE_DIR)+'/media/'+imagename

            with open(food_folder, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)
    if finaldata.get('symptoms'):
        if len(finaldata.get('symptoms')) > 0:
            rezepteSymptoms = RezepteSymptome.objects.filter(rezepteId=rezepte)
            RezepteSymptome.objects.filter(rezepteId=rezepte).delete()
            for key in finaldata["symptoms"]:
                symptom = Symptom.objects.get(id=int(key))
                rezepteSymptom = RezepteSymptome(rezepteId=rezepte, symptomeId=symptom)
                rezepteSymptom.save()
    if finaldata.get('allergies'):
        if len(finaldata.get('allergies')) > 0:
            rezepteHandicaps = RezepteHandicap.objects.filter(rezepteId=rezepte)
            RezepteHandicap.objects.filter(rezepteId=rezepte).delete()
            for key in finaldata["allergies"]:
                handicap = Handicap.objects.get(id=int(key))
                rezepteHandicap = RezepteHandicap(rezepteId=rezepte, handicapId=handicap)
                rezepteHandicap.save()

    response = JsonResponse({},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getHandicap(request):
    handicaps = Handicap.objects.all()

    handicapList = []

    for handicap in handicaps:
        handicapDict = {}
        handicapDict["id"] = handicap.id
        handicapDict["name"] = handicap.namen
        handicapList.append(handicapDict)

    response = JsonResponse(handicapList, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getLebensmittel(request):
    lebensmittels = Lebensmittel.objects.all()

    lebensmittelList = []

    for lebensmittel in lebensmittels:
        lebensmittelDict = {}
        lebensmittelDict["id"] = lebensmittel.id
        lebensmittelDict["name"] = lebensmittel.name
        lebensmittelList.append(lebensmittelDict)

    response = JsonResponse(lebensmittelList, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getSymptoms(request):
    symptoms = Symptom.objects.all()

    symptompList = []

    for symptom in symptoms:
        symptomlDict = {}
        symptomlDict["id"] = symptom.id
        symptomlDict["name"] = symptom.namen
        symptompList.append(symptomlDict)

    response = JsonResponse(symptompList, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["GET"])
def getAllRezepte(request):
    rezeptes = Rezepte.objects.all()
    pageno = request.GET.get('page', 1)
    paginator = Paginator(rezeptes, 5)
    rezeptes = paginator.page(pageno)

    rezepteResult = {}
    rezepteResult["pages"] = paginator.num_pages;
    rezepteResult["count"] = paginator.count;
    rezeptelList = []

    for rezepte in rezeptes:
        rezepteDict = createRezepteResponseFromRezepteObject(rezepte)
        rezeptelList.append(rezepteDict)
    rezepteResult["rezeptes"] = rezeptelList;

    response = JsonResponse(rezepteResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["GET"])
def getRezepteById(request, receipeid):
    rezepte = Rezepte.objects.get(id=receipeid)
    rezepteDict = createRezepteResponseFromRezepteObject(rezepte)
    response = JsonResponse(rezepteDict, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response



def createRezepteResponseFromRezepteObject(rezepte):
    rezepteDict = {}
    rezepteDict["id"] = rezepte.id
    rezepteDict["namen"] = rezepte.namen
    rezepteDict["beschreibung"] = rezepte.beschreibung
    rezepteDict["buchlink"] = rezepte.buch_link
    rezepteDict["buchauthor"] = rezepte.buch_author
    rezepteDictFoodList = []
    rezepteLebensmittels = RezepteLebensmittel.objects.filter(rezepteId=rezepte)
    for rezepteLebensmitte in rezepteLebensmittels:
        rezepteFoodDict = {}
        rezepteFoodDict["rezepteLebensmitteId"] = rezepteLebensmitte.lebensmittelId.id
        rezepteFoodDict["rezepteLebensmitteName"] = rezepteLebensmitte.lebensmittelId.name
        rezepteFoodDict["bild_link"] = rezepteLebensmitte.bild_link
        rezepteFoodDict["menge"] = rezepteLebensmitte.menge
        rezepteDictFoodList.append(rezepteFoodDict)
    rezepteDict["rezepteDictFoodList"] = rezepteDictFoodList

    rezepteDict["symptomList"] = []
    rezepteDict["symptomNameList"] = []
    rezepteSymptoms = RezepteSymptome.objects.filter(rezepteId=rezepte)
    for rezepteSymptom in rezepteSymptoms:
        if rezepteSymptom.symptomeId.id:
            rezepteDict["symptomList"].append(rezepteSymptom.symptomeId.id)
            rezepteDict["symptomNameList"].append(rezepteSymptom.symptomeId.namen)

    rezepteDict["handicapList"] = []
    rezepteDict["handicapNameList"] = []
    rezepteHandicaps = RezepteHandicap.objects.filter(rezepteId=rezepte)
    for rezepteHandicap in rezepteHandicaps:
        if rezepteHandicap.handicapId.id:
            rezepteDict["handicapList"].append(rezepteHandicap.handicapId.id)
            rezepteDict["handicapNameList"].append(rezepteHandicap.handicapId.namen)



    return rezepteDict



@api_view(["POST"])
def updateReceipe(request, receipeid):
    finaldata = {}
    requestdata = dict(request.POST)
    finaldata["symptoms"] = []
    finaldata["allergies"] = []
    for index in requestdata:
        indexsplit = index.split("|")
        if len(indexsplit) > 1:
            if indexsplit[0] == "food":
                if finaldata.get("food") is None:
                    finaldata["food"] = {}
                if  finaldata["food"].get(indexsplit[1]) is None:
                    finaldata["food"][indexsplit[1]] = {}
                finaldata["food"][indexsplit[1]][indexsplit[2]] = requestdata["food"+"|"+indexsplit[1]+"|"+indexsplit[2]]
            if indexsplit[0] == "symptoms":
                finaldata["symptoms"].append(requestdata["symptoms"+"|"+indexsplit[1]][0])
            if indexsplit[0] == "allergies":
                finaldata["allergies"].append(requestdata["allergies"+"|"+indexsplit[1]][0])
        else:
            finaldata[index] = requestdata[index]

    rezepte = Rezepte.objects.get(id=receipeid)
    setattr(rezepte, "namen", finaldata["title"][0])
    setattr(rezepte, "beschreibung", finaldata["beschreibung"][0])
    setattr(rezepte, "updated", time.time())

    if finaldata.get("buchlink"):
        setattr(rezepte, "buch_link",  finaldata["buchlink"][0])
    if finaldata.get("buchauthor"):
        setattr(rezepte, "buch_author", finaldata["buchauthor"][0])

    rezepte.save()




    if  finaldata.get('food'):
        rezepteLebensmittels = RezepteLebensmittel.objects.filter(rezepteId=rezepte)
        for rezepteLebensmitte in rezepteLebensmittels:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, rezepteLebensmitte.bild_link))
            except:
                pass
        RezepteLebensmittel.objects.filter(rezepteId=rezepte).delete()

        for key in finaldata["food"]:
            if finaldata["food"][key].get('food_image_name'):
                imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
                imagename = str(rezepte.id) + imagename
                lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
                rezepteLebensmittel = RezepteLebensmittel(rezepteId=rezepte, lebensmittelId=lebensmittel,menge=finaldata["food"][key]['quantity'][0],bild_link=imagename)
                rezepteLebensmittel.save()




        for fileIndex in request.FILES:
            img = request.FILES[fileIndex]
            img_extension = os.path.splitext(img.name)[1]
            imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)
            imagename = str(rezepte.id) + imagename
            food_folder = str(settings.BASE_DIR)+'/media/'+imagename

            with open(food_folder, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)

    if len(finaldata.get('symptoms')) > 0:
        rezepteSymptoms = RezepteSymptome.objects.filter(rezepteId=rezepte)
        RezepteSymptome.objects.filter(rezepteId=rezepte).delete()
        for key in finaldata["symptoms"]:
            symptom = Symptom.objects.get(id=int(key))
            rezepteSymptom = RezepteSymptome(rezepteId=rezepte, symptomeId=symptom)
            rezepteSymptom.save()

    if len(finaldata.get('allergies')) > 0:
        rezepteHandicaps = RezepteHandicap.objects.filter(rezepteId=rezepte)
        RezepteHandicap.objects.filter(rezepteId=rezepte).delete()
        for key in finaldata["allergies"]:
            handicap = Handicap.objects.get(id=int(key))
            rezepteHandicap = RezepteHandicap(rezepteId=rezepte, handicapId=handicap)
            rezepteHandicap.save()



    response = JsonResponse({},safe=False);
    #response.set_cookie('fdiarysess', cookie)

    return response





@api_view(["POST"])
def deleteReceipe(request, receipeid):
    rezepte = Rezepte.objects.get(id=receipeid)


    rezepteLebensmittels = RezepteLebensmittel.objects.filter(rezepteId=rezepte)
    for rezepteLebensmitte in rezepteLebensmittels:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, rezepteLebensmitte.bild_link))
        except:
            pass
    RezepteLebensmittel.objects.filter(rezepteId=rezepte).delete()
    RezepteSymptome.objects.filter(rezepteId=rezepte).delete()
    RezepteHandicap.objects.filter(rezepteId=rezepte).delete()
    rezepte.delete()

    response = JsonResponse({}, safe=False);

    return  response




