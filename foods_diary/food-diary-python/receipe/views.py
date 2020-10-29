from django.shortcuts import render

from rest_framework.decorators import api_view
from django.http import JsonResponse
import uuid
import os
import re
from django.conf import settings
from receipe.models import Lebensmittel, Rezepte, RezepteLebensmittel;
from django.core.paginator import Paginator



import json



@api_view(["POST"])
def createReceipe(request):
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
    rezepte = Rezepte(namen=finaldata["title"][0], beschreibung=finaldata["beschreibung"][0])
    rezepte.save()

    for key in finaldata["food"]:
        imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
        lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
        rezepteLebensmittel = RezepteLebensmittel(rezepteId=rezepte, lebensmittelId=lebensmittel,menge=finaldata["food"][key]['quantity'][0],bild_link=imagename,id=rezepte.id)
        rezepteLebensmittel.save()




    for fileIndex in request.FILES:
        img = request.FILES[fileIndex]
        img_extension = os.path.splitext(img.name)[1]
        imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)

        food_folder = str(settings.BASE_DIR)+'/media/'+imagename

        with open(food_folder, 'wb+') as f:
            for chunk in img.chunks():
                f.write(chunk)



    response = JsonResponse({},safe=False);
    #response.set_cookie('fdiarysess', cookie)

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
    return rezepteDict



@api_view(["POST"])
def updateReceipe(request, receipeid):
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

    rezepte = Rezepte.objects.get(id=receipeid)
    setattr(rezepte, "namen", finaldata["title"][0])
    setattr(rezepte, "beschreibung", finaldata["beschreibung"][0])
    rezepte.save()

    rezepteLebensmittels = RezepteLebensmittel.objects.filter(rezepteId=rezepte)
    for rezepteLebensmitte in rezepteLebensmittels:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, rezepteLebensmitte.bild_link))
        except:
            pass
    RezepteLebensmittel.objects.filter(rezepteId=rezepte).delete()



    for key in finaldata["food"]:
        imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
        lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
        rezepteLebensmittel = RezepteLebensmittel(rezepteId=rezepte, lebensmittelId=lebensmittel,menge=finaldata["food"][key]['quantity'][0],bild_link=imagename)
        rezepteLebensmittel.save()




    for fileIndex in request.FILES:
        img = request.FILES[fileIndex]
        img_extension = os.path.splitext(img.name)[1]
        imagename = re.sub('[^A-Za-z0-9\.]+', '', img.name)

        food_folder = str(settings.BASE_DIR)+'/media/'+imagename

        with open(food_folder, 'wb+') as f:
            for chunk in img.chunks():
                f.write(chunk)



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

    rezepte.delete()

    response = JsonResponse({}, safe=False);

    return  response




