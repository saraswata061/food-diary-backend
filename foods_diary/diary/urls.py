from django.urls import path

from .views import getMahlzeiten, getEmotion, getAllBuch, getBuchById, updateDiary, createDiary, deleteBuch,searchDiary


urlpatterns = [
    path('getMahlzeiten/', getMahlzeiten),
    path('getEmotion/', getEmotion),
    path('getAllBuch/', getAllBuch),
    path(r'getBuchById/<int:buchid>', getBuchById),
    path(r'updateDiary/<int:buchid>', updateDiary),
    path(r'deleteDiary/<int:buchid>', deleteBuch),
    path(r'createDiary/', createDiary),
    path(r'searchDiary/',searchDiary),

]
