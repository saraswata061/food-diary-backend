"""foods_diary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from user import views as user_views
from receipe import views as receipe_views

from diary import views as diary_views
from django.conf import settings
from django.conf.urls.static import static

PATH = '/static/'
ROOT = str(settings.BASE_DIR)+'/static/food_image/'


urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'api/user/', include('user.urls')),
    path(r'api/diary/', include('diary.urls')),
    path(r'api/logout/',user_views.logout),
    path(r'api/receipe/lebensmittels',receipe_views.getLebensmittel),
    path(r'api/receipe/getLebensmittelPagination/',receipe_views.getLebensmittelPagination),
    path(r'api/receipe/getHandicapPagination/',receipe_views.getHandicapPagination),
    path(r'api/receipe/getSymptoms/',receipe_views.getSymptoms),
    path(r'api/receipe/searchRezepte/',receipe_views.searchRezepte),
    path(r'api/receipe/getLebensmittelById/<int:lebensmittelId>',receipe_views.getLebensmittelById),
    path(r'api/receipe/getHandicapById/<int:handicapId>',receipe_views.getHandicapById),
    path(r'api/receipe/createUpdateLebensmittel/',receipe_views.createUpdateLebensmittel),
    path(r'api/receipe/createUpdateHandicap/',receipe_views.createUpdateHandicap),
    path(r'api/receipe/getHandicap/',receipe_views.getHandicap),
    path(r'api/receipe/get/id/<int:receipeid>', receipe_views.getRezepteById),
    path(r'api/receipe/get/all',receipe_views.getAllRezepte),
    path(r'api/receipe/update/<int:receipeid>',receipe_views.updateReceipe),
    path(r'api/receipe/delete/<int:receipeid>',receipe_views.deleteReceipe),
    path(r'api/receipe/',receipe_views.createReceipe),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


