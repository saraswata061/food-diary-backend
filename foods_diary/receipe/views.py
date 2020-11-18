from django.shortcuts import render

from rest_framework.decorators import api_view
from django.http import JsonResponse
import uuid
import os
import re
from django.conf import settings
from receipe.models import Lebensmittel, Rezepte, RezepteLebensmittel, Handicap, Symptom, RezepteSymptome, RezepteHandicap, HandicapSymptome, HandicapLebensmittel;
from django.core.paginator import Paginator

from django.db.models import Q

import time



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
                if indexsplit[2] == "selectedFood":
                    continue
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
    is_public = False
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


    if getCurrentUserInfo(request)['role'] == "admin":
        is_public = True
    rezepte = Rezepte(namen=finaldata["title"][0], beschreibung=finaldata["beschreibung"][0],updated=time.time(), buch_link=buchlink, buch_author=buchauthor,author= getCurrentUserInfo(request)['user_id'],isPublic = is_public)
    rezepte.save()


    if  finaldata.get('food'):
        rezepteLebensmittels = RezepteLebensmittel.objects.filter(rezepteId=rezepte)
        for rezepteLebensmitte in rezepteLebensmittels:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, rezepteLebensmitte.bild_link))
            except:
                pass
        RezepteLebensmittel.objects.filter(rezepteId=rezepte).delete()

        updateRezepteFoodList(finaldata, request, rezepte)
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
def getHandicapPagination(request):
    handicapsreq = request.GET.get("handicaps", None)

    if handicapsreq:
        handicapList = [int(i) for i in handicapsreq.split(',') if i.strip() != ""]
        handicaps = Handicap.objects.filter()
        handicaps = handicaps.filter(id__in=handicapList)

    else:
        handicaps = Handicap.objects.all()

    pageno = request.GET.get('page', 1)
    paginator = Paginator(handicaps, 5)
    handicaps = paginator.page(pageno)

    handicapResult = {}
    handicapResult["pages"] = paginator.num_pages;
    handicapResult["count"] = paginator.count;


    handicapList = []

    for handicap in handicaps:
        handicapDict = {}
        handicapDict["id"] = handicap.id
        handicapDict["name"] = handicap.namen
        handicapList.append(handicapDict)
    handicapResult["handicaps"] = handicapList;

    response = JsonResponse(handicapResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["GET"])
def getLebensmittelPagination(request):
    lebensmittelsreq = request.GET.get("lebensmittels", None)

    if lebensmittelsreq:
        lebensmittelList = [int(i) for i in lebensmittelsreq.split(',') if i.strip() != ""]
        lebensmittels = Lebensmittel.objects.filter()
        lebensmittels = lebensmittels.filter(id__in=lebensmittelList)

    else:
        lebensmittels = Lebensmittel.objects.all()

    pageno = request.GET.get('page', 1)
    paginator = Paginator(lebensmittels, 5)
    lebensmittels = paginator.page(pageno)

    lebensmittelResult = {}
    lebensmittelResult["pages"] = paginator.num_pages;
    lebensmittelResult["count"] = paginator.count;
    buchlList = []

    lebensmittelList = []

    for lebensmittel in lebensmittels:
        lebensmittelDict = {}
        lebensmittelDict["id"] = lebensmittel.id
        lebensmittelDict["name"] = lebensmittel.name
        lebensmittelList.append(lebensmittelDict)
    lebensmittelResult["lebensmittels"] = lebensmittelList;

    response = JsonResponse(lebensmittelResult, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["POST"])
def createUpdateHandicap(request):
    finaldata = {}
    finaldata["goodfoods"] = []
    finaldata["badfoods"] = []
    finaldata["symptoms"] = []
    requestdata = dict(request.POST)
    for index in requestdata:
        indexsplit = index.split("|")
        if len(indexsplit) > 1:
            if indexsplit[0] == "goodfoods":
                finaldata["goodfoods"].append(requestdata["goodfoods" + "|" + indexsplit[1]][0])
            if indexsplit[0] == "badfoods":
                finaldata["badfoods"].append(requestdata["badfoods" + "|" + indexsplit[1]][0])
            if indexsplit[0] == "symptoms":
                finaldata["symptoms"].append(requestdata["symptoms" + "|" + indexsplit[1]][0])
        else:
            finaldata[index] = requestdata[index]
    handicap = None
    if int(finaldata.get("id")[0]) != 0:
        handicap = Handicap.objects.get(id=finaldata["id"][0])
        setattr(handicap, "namen", finaldata["name"][0])

    else:
        handicap = Handicap(
            namen=finaldata["name"][0]
        )

        handicap.save()

    if len(finaldata.get('goodfoods')) > 0:
        HandicapLebensmittel.objects.filter(handicapId=handicap, isGood=True).delete()
        for key in finaldata["goodfoods"]:
            lebensmittel = Lebensmittel.objects.get(id=int(key))
            handicapLebensmittel = HandicapLebensmittel(handicapId=handicap, lebensmittelId=lebensmittel, isGood=True, isBad=False)
            handicapLebensmittel.save()

    if len(finaldata.get('badfoods')) > 0:
        HandicapLebensmittel.objects.filter(handicapId=handicap, isBad=True).delete()
        for key in finaldata["badfoods"]:
            lebensmittel = Lebensmittel.objects.get(id=int(key))
            handicapLebensmittel = HandicapLebensmittel(handicapId=handicap, lebensmittelId=lebensmittel, isBad=True, isGood=False)
            handicapLebensmittel.save()

    if len(finaldata.get('symptoms')) > 0:
        handicapSymptome = HandicapSymptome.objects.filter(handicapId=handicap)
        HandicapSymptome.objects.filter(handicapId=handicap).delete()
        for key in finaldata["symptoms"]:
            symptom = Symptom.objects.get(id=int(key))
            handicapSymptome = HandicapSymptome(handicapId=handicap, symptomeId=symptom)
            handicapSymptome.save()

    handicap.save()

    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response

@api_view(["POST"])
def handicapLebensmittel(request):
    finaldata = {}

    finaldata["handicps"] = []
    finaldata['handicapList'] = []
    requestdata = dict(request.POST)
    for index in requestdata:
        indexsplit = index.split("|")
        if len(indexsplit) > 1:
            if indexsplit[0] == "handicps":
                finaldata["handicps"].append(requestdata["handicps" + "|" + indexsplit[1]][0])

        else:
            finaldata[index] = requestdata[index]

    for key in finaldata["handicps"]:
        handicapResp = getHandcapFoodSuggestion(int(key))
        finaldata['handicapList'] = handicapResp



    response = JsonResponse(finaldata, safe=False)
    return response



def getHandcapFoodSuggestion(handicap_id):
    handicap = Handicap.objects.get(id=handicap_id);
    handicapLebensmittels = HandicapLebensmittel.objects.filter(handicapId=handicap)
    handicapGoodFoodList = []
    handicapBadFoodList = []
    handicapResp = {}
    for handicapLebensmittel in handicapLebensmittels:
        handicapFoodDict = {}
        handicapFoodDict["id"] = handicapLebensmittel.lebensmittelId.id
        handicapFoodDict["name"] = handicapLebensmittel.lebensmittelId.name
        if handicapLebensmittel.isGood:
            handicapGoodFoodList.append(handicapFoodDict["name"])
        if handicapLebensmittel.isBad:
            handicapBadFoodList.append(handicapFoodDict["name"])
    handicapResp['goodFoodList'] = handicapGoodFoodList
    handicapResp['badFoodList'] = handicapBadFoodList
    handicapResp['handicap_id'] = int(handicap_id)
    return handicapResp


@api_view(["POST"])
def createUpdateLebensmittel(request):
    finaldata = {}
    requestdata = dict(request.POST)
    for index in requestdata:
        finaldata[index] = requestdata[index]

    try:
        value = float(finaldata.get('weight')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Weight can only be float"]}, safe=False, status=500);

    try:
        value = float(finaldata.get('calories')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Calories can only be float"]}, safe=False, status=500);


    try:
        value = float(finaldata.get('kilojoule')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Kilojoule can only be float"]}, safe=False, status=500);

    try:
        value = float(finaldata.get('breadunit')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Breadunit can only be float"]}, safe=False, status=500);

    try:
        value = float(finaldata.get('carbohydrates')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Carbohydrates can only be float"]}, safe=False, status=500);


    try:
        value = float(finaldata.get('protein')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Protein can only be float"]}, safe=False, status=500);


    try:
        value = float(finaldata.get('csalary')[0])
    except ValueError:
        return JsonResponse({"messageList": ["Csalary can only be float"]}, safe=False, status=500);

    if int(finaldata.get("id")[0]) != 0:
        lebensmittel = Lebensmittel.objects.get(id=finaldata["id"][0])
        setattr(lebensmittel, "name", finaldata["name"][0])
        setattr(lebensmittel, "weight", finaldata["weight"][0])
        setattr(lebensmittel, "calories", finaldata["calories"][0])
        setattr(lebensmittel, "kilojoule", finaldata["kilojoule"][0])
        setattr(lebensmittel, "breadunit", finaldata["breadunit"][0])
        setattr(lebensmittel, "carbohydrates", finaldata["carbohydrates"][0])
        setattr(lebensmittel, "bold", finaldata["bold"][0])
        setattr(lebensmittel, "protein", finaldata["protein"][0])
        setattr(lebensmittel, "csalary", finaldata["csalary"][0])
        setattr(lebensmittel, "animal", 1 if (finaldata["animal"][0] == "true") else 0)
        setattr(lebensmittel, "milk", 1 if (finaldata["milk"][0] == "true") else 0)
        setattr(lebensmittel, "fish", 1 if (finaldata["fish"][0] == "true") else 0)
        setattr(lebensmittel, "fruit", 1 if (finaldata["fruit"][0] == "true") else 0)
        setattr(lebensmittel, "vegetables", 1 if (finaldata["vegetables"][0] == "true") else 0)
        setattr(lebensmittel, "spice", 1 if (finaldata["spice"][0] == "true") else 0)
        setattr(lebensmittel, "herbs", 1 if (finaldata["herbs"][0] == "true") else 0)
        setattr(lebensmittel, "court", 1 if (finaldata["herbs"][0] == "true") else 0)
        setattr(lebensmittel, "vegan", 1 if (finaldata["vegan"][0] == "true") else 0)
        setattr(lebensmittel, "vegetarian", 1 if (finaldata["vegetarian"][0] == "true") else 0)
        setattr(lebensmittel, "shellfish", 1 if (finaldata["shellfish"][0] == "true") else 0)
        setattr(lebensmittel, "sauce", 1 if (finaldata["sauce"][0] == "true") else 0)
        setattr(lebensmittel, "cooked", 1 if (finaldata["cooked"][0] == "true") else 0)
        setattr(lebensmittel, "fried", 1 if (finaldata["fried"][0] == "true") else 0)
        setattr(lebensmittel, "grilled", 1 if (finaldata["grilled"][0] == "true") else 0)
        setattr(lebensmittel, "fermented", 1 if (finaldata["fermented"][0] == "true") else 0)
        setattr(lebensmittel, "basic", 1 if (finaldata["basic"][0] == "true") else 0)
        setattr(lebensmittel, "acidic", 1 if (finaldata["acidic"][0] == "true") else 0)
        setattr(lebensmittel, "baked", 1 if (finaldata["baked"][0] == "true") else 0)
        setattr(lebensmittel, "smoked", 1 if (finaldata["smoked"][0] == "true") else 0)
        setattr(lebensmittel, "cereals", 1 if (finaldata["cereals"][0] == "true") else 0)
        setattr(lebensmittel, "selfmade", 1 if (finaldata["selfmade"][0] == "true") else 0)
        setattr(lebensmittel, "ironcontent", 1 if (finaldata["ironcontent"][0] == "true") else 0)
        setattr(lebensmittel, "hasiron", 1 if (finaldata["hasiron"][0] == "true") else 0)
        setattr(lebensmittel, "hasc", 1 if (finaldata["hasc"][0] == "true") else 0)
        setattr(lebensmittel, "nuts", 1 if (finaldata["nuts"][0] == "true") else 0)
        setattr(lebensmittel, "lactose", 1 if (finaldata["lactose"][0] == "true") else 0)
        setattr(lebensmittel, "wheat", 1 if (finaldata["wheat"][0] == "true") else 0)
        setattr(lebensmittel, "gluten", 1 if (finaldata["gluten"][0] == "true") else 0)
        setattr(lebensmittel, "fructose", 1 if (finaldata["fructose"][0] == "true") else 0)
    else:
        lebensmittel = Lebensmittel(
            name=finaldata["name"][0],
            weight= finaldata["weight"][0],
            calories= finaldata["calories"][0],
            kilojoule=finaldata["kilojoule"][0],
            breadunit= finaldata["breadunit"][0],
            carbohydrates= finaldata["carbohydrates"][0],
            bold=finaldata["bold"][0],
            protein=finaldata["protein"][0],
            csalary= finaldata["csalary"][0],
            animal= 1 if (finaldata["animal"][0] == "true") else 0,
            milk=1 if (finaldata["milk"][0] == "true") else 0,
            fish= 1 if (finaldata["fish"][0] == "true") else 0,
            fruit= 1 if (finaldata["fruit"][0] == "true") else 0,
            vegetables= 1 if (finaldata["vegetables"][0] == "true") else 0,
            spice= 1 if (finaldata["spice"][0] == "true") else 0,
            herbs= 1 if (finaldata["herbs"][0] == "true") else 0,
            court= 1 if (finaldata["herbs"][0] == "true") else 0,
            vegan=1 if (finaldata["vegan"][0] == "true") else 0,
            vegetarian= 1 if (finaldata["vegetarian"][0] == "true") else 0,
            shellfish= 1 if (finaldata["shellfish"][0] == "true") else 0,
            sauce=1 if (finaldata["sauce"][0] == "true") else 0,
            raw=1 if (finaldata["raw"][0] == "true") else 0,
            cooked=1 if (finaldata["cooked"][0] == "true") else 0,
            fried=1 if (finaldata["fried"][0] == "true") else 0,
            grilled=1 if (finaldata["grilled"][0] == "true") else 0,
            fermented=1 if (finaldata["fermented"][0] == "true") else 0,
            basic=1 if (finaldata["basic"][0] == "true") else 0,
            acidic=1 if (finaldata["acidic"][0] == "true") else 0,
            neutral=1 if (finaldata["neutral"][0] == "true") else 0,
            baked= 1 if (finaldata["baked"][0] == "true") else 0,
            smoked=1 if (finaldata["smoked"][0] == "true") else 0,
            cereals=1 if (finaldata["cereals"][0] == "true") else 0,
            selfmade=1 if (finaldata["selfmade"][0] == "true") else 0,
            ironcontent=1 if (finaldata["ironcontent"][0] == "true") else 0,
            hasiron=1 if (finaldata["hasiron"][0] == "true") else 0,
            hasc=1 if (finaldata["hasc"][0] == "true") else 0,
            nuts=1 if (finaldata["nuts"][0] == "true") else 0,
            lactose=1 if (finaldata["lactose"][0] == "true") else 0,
            wheat=1 if (finaldata["wheat"][0] == "true") else 0,
            gluten=1 if (finaldata["gluten"][0] == "true") else 0,
            fructose=1 if (finaldata["fructose"][0] == "true") else 0
        )

    lebensmittel.save()

    response = JsonResponse({}, safe=False);
    # response.set_cookie('fdiarysess', cookie)

    return response


@api_view(["GET"])
def getLebensmittelById(request,lebensmittelId):
    lebensmittel = Lebensmittel.objects.get(id=lebensmittelId)
    response  = createLebensmittel(lebensmittel)
    return JsonResponse(response, safe=False);


@api_view(["GET"])
def getHandicapById(request,handicapId):
    handicap = Handicap.objects.get(id=handicapId)
    response  = createHandicap(handicap)
    return JsonResponse(response, safe=False);

def createLebensmittel(lebensmittel):
    lebensmittelDict = {}
    lebensmittelDict["name"] = lebensmittel.name
    lebensmittelDict["weight"] = lebensmittel.weight
    lebensmittelDict["calories"] = lebensmittel.calories
    lebensmittelDict["kilojoule"] = lebensmittel.kilojoule
    lebensmittelDict["breadunit"] = lebensmittel.breadunit
    lebensmittelDict["carbohydrates"] = lebensmittel.carbohydrates
    lebensmittelDict["bold"] = lebensmittel.bold
    lebensmittelDict["protein"] = lebensmittel.protein
    lebensmittelDict["csalary"] = lebensmittel.csalary
    lebensmittelDict["animal"] = lebensmittel.animal
    lebensmittelDict["milk"] = lebensmittel.milk
    lebensmittelDict["fish"] = lebensmittel.fish
    lebensmittelDict["fruit"] = lebensmittel.fruit
    lebensmittelDict["vegetables"] = lebensmittel.vegetables
    lebensmittelDict["spice"] = lebensmittel.spice
    lebensmittelDict["herbs"] = lebensmittel.herbs
    lebensmittelDict["court"] = lebensmittel.court
    lebensmittelDict["vegan"] = lebensmittel.vegan
    lebensmittelDict["vegetarian"] = lebensmittel.vegetarian
    lebensmittelDict["shellfish"] = lebensmittel.shellfish
    lebensmittelDict["sauce"] = lebensmittel.sauce
    lebensmittelDict["raw"] = lebensmittel.raw
    lebensmittelDict["cooked"] = lebensmittel.cooked
    lebensmittelDict["fried"] = lebensmittel.fried
    lebensmittelDict["grilled"] = lebensmittel.grilled
    lebensmittelDict["fermented"] = lebensmittel.fermented
    lebensmittelDict["basic"] = lebensmittel.basic
    lebensmittelDict["acidic"] = lebensmittel.acidic
    lebensmittelDict["neutral"] = lebensmittel.neutral
    lebensmittelDict["baked"] = lebensmittel.baked
    lebensmittelDict["smoked"] = lebensmittel.smoked
    lebensmittelDict["cereals"] = lebensmittel.cereals
    lebensmittelDict["selfmade"] = lebensmittel.selfmade
    lebensmittelDict["ironcontent"] = lebensmittel.ironcontent
    lebensmittelDict["hasiron"] = lebensmittel.hasiron
    lebensmittelDict["hasc"] = lebensmittel.hasc
    lebensmittelDict["nuts"] = lebensmittel.nuts
    lebensmittelDict["lactose"] = lebensmittel.lactose
    lebensmittelDict["wheat"] = lebensmittel.wheat
    lebensmittelDict["gluten"] = lebensmittel.gluten
    lebensmittelDict["fructose"] = lebensmittel.fructose

    return lebensmittelDict



def createHandicap(handicap):
    handicapDict = {}
    handicapDict["name"] = handicap.namen
    handicapDict["id"] = handicap.id
    handicapDictGoodFoodList = []

    handicapGoodLebensmittels = HandicapLebensmittel.objects.filter(handicapId=handicap, isGood=True)

    for handicapGoodLebensmittel in handicapGoodLebensmittels:
        handicapFoodDict = {}
        handicapFoodDict["id"] = handicapGoodLebensmittel.lebensmittelId.id
        handicapFoodDict["name"] = handicapGoodLebensmittel.lebensmittelId.name
        handicapDictGoodFoodList.append(handicapFoodDict)
    handicapDict["handicapDictGoodFoodList"] = handicapDictGoodFoodList

    handicapDictBadFoodList = []
    handicapBadLebensmittels = HandicapLebensmittel.objects.filter(handicapId=handicap, isBad=True)

    for handicapBadLebensmittel in handicapBadLebensmittels:
        handicapFoodDict = {}
        handicapFoodDict["id"] = handicapBadLebensmittel.lebensmittelId.id
        handicapFoodDict["name"] = handicapBadLebensmittel.lebensmittelId.name
        handicapDictBadFoodList.append(handicapFoodDict)
    handicapDict["handicapBadDictBadFoodList"] = handicapDictBadFoodList

    handicapDictSymptomeList = []
    handicapSymptoms = HandicapSymptome.objects.filter(handicapId=handicap)
    for handicapSymptom in handicapSymptoms:
        handicapSymptomDict = {}
        handicapSymptomDict["id"] = handicapSymptom.symptomeId.id
        handicapSymptomDict["name"] = handicapSymptom.symptomeId.namen
        handicapDictSymptomeList.append(handicapSymptomDict)
    handicapDict["symptomList"] = handicapDictSymptomeList

    return handicapDict


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
    if getCurrentUserInfo(request)['role'] == 'admin':
        rezeptes = Rezepte.objects.all()
    elif getCurrentUserInfo(request)['role'] == 'client':
        rezeptes = Rezepte.objects.filter(isPublic=True)
    else:
        rezeptes = Rezepte.objects.filter(Q(author=getCurrentUserInfo(request)['user_id']) | Q(isPublic=True))
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
def searchRezepte(request):
    title = request.GET.get("title","")
    description = request.GET.get("description","")
    symptoms = request.GET.get("symptoms", "")
    lebensmittels = request.GET.get("lebensmittels", "")
    symptomList = [Symptom.objects.get(id=int(i)) for i in symptoms.split(',') if i.strip() != ""]
    lebensmittelList = [Lebensmittel.objects.get(id=int(i)) for i in lebensmittels.split(',') if i.strip() != ""]


    rezeptes = None
    rezeptes = Rezepte.objects.filter()

    if getCurrentUserInfo(request)['role'] == 'admin':
        pass
    elif getCurrentUserInfo(request)['role'] == 'client':
        rezeptes = rezeptes.filter(isPublic=True)
    else:
        rezeptes = rezeptes.filter(Q(author=getCurrentUserInfo(request)['user_id']) | Q(isPublic=True))



    if len(title):
        rezeptes = rezeptes.filter(namen__contains=title)
    if len(description):
        rezeptes = rezeptes.filter(beschreibung__contains=description)
    if len(symptomList) > 0:
        rezeptes = rezeptes.filter(rezepte_symptom__symptomeId__in=symptomList)
    if len(lebensmittelList) > 0:
        rezeptes = rezeptes.filter(rezepte_lebensmittel__lebensmittelId__in=lebensmittelList)

    rezeptelList = []
    rezepteResult = {}

    for rezepte in rezeptes:
        rezepteDict = createRezepteResponseFromRezepteObject(rezepte)
        rezeptelList.append(rezepteDict)
    rezepteResult["rezeptes"] = rezeptelList;
    rezepteResult["count"] = len(rezeptelList);
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
    if rezepte:
        if rezepte.id:
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
                if indexsplit[2] == "selectedFood":
                    continue
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


    rezepte.save()

    if finaldata.get('food'):
        rezepteLebensmittels = RezepteLebensmittel.objects.filter(rezepteId=rezepte)
        for rezepteLebensmitte in rezepteLebensmittels:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, rezepteLebensmitte.bild_link))
            except:
                pass
        RezepteLebensmittel.objects.filter(rezepteId=rezepte).delete()

        updateRezepteFoodList(finaldata, request, rezepte)






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




def updateRezepteFoodList(finaldata, request, entity):
    for key in finaldata["food"]:
        imagename = ""
        quantity = "";
        lebensmittel = Lebensmittel.objects.get(id=int(finaldata["food"][key]['food'][0]))
        if finaldata["food"][key].get('quantity'):
            measure = "gm";
            if finaldata["food"][key].get('measure'):
                measure = finaldata["food"][key]['measure'][0]
            quantity = finaldata["food"][key]['quantity'][0]+" "+measure
        if finaldata["food"][key].get('food_image_name'):
            imagename = re.sub('[^A-Za-z0-9\.]+', '', finaldata["food"][key]['food_image_name'][0])
            imagename = str(entity.id) + imagename

        entityLebensmittel = RezepteLebensmittel(rezepteId=entity, lebensmittelId=lebensmittel, menge=quantity,
                                            bild_link=imagename)
        entityLebensmittel.save()
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




