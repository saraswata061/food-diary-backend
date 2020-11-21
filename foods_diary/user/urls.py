from django.urls import path

from .views import StripeAuthorizeView, StripeAuthorizeCallbackView, user, getFAQById,getAllFAQ,deleteFAQ, PersonDetailView, coachingRequest, getCoachingRequests, getCoachingRequestsById,  searchUser, UserChargeView, createUser, deleteUser, getAllUser, getCurrentUer, updateUserProfile,getUserChatMessages, csrf, appendUserChat, saveFAQ


urlpatterns = [
  path('', getAllUser),
  path('updateProfile/', updateUserProfile),
  path('appendUserChat/', appendUserChat),
  path('saveFAQ/', saveFAQ),
  path('getFAQById/<int:faqid>', getFAQById),
  path('faq/all', getAllFAQ),
  path('faq/delete/<int:faqid>', deleteFAQ),

  path('getUserChatMessages/', getUserChatMessages),
  path('searchUser/', searchUser),
  path('getCurrentUer/', getCurrentUer),
  path('searchPersons/', getCurrentUer),
  path('csrf/', csrf),
  path('<int:userid>/', user),
  path('createUser', createUser),
  path('saveCoachingRequest/', coachingRequest),
  path('getCoachingRequests/<int:coachid>/<int:clientid>', getCoachingRequests),
  path('getCoachingRequestsById/<int:requestid>', getCoachingRequestsById),
  path('deleteUser/<int:userid>/', deleteUser),
  path('authorize/', StripeAuthorizeView.as_view(), name='authorize'),
  path('oauth/callback/', StripeAuthorizeCallbackView.as_view(), name='authorize_callback'),
  path('charge/', UserChargeView.as_view(), name='charge'),
  path('<int:pk>/', PersonDetailView.as_view(), name='person_detail'),

]
