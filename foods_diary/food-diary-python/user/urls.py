from django.urls import path

from .views import StripeAuthorizeView, StripeAuthorizeCallbackView, user, PersonDetailView, UserChargeView, createUser, deleteUser, getAllUser, getCurrentUer


urlpatterns = [
  path('', getAllUser),
  path('getCurrentUer/', getCurrentUer),
  path('<int:userid>/', user),
  path('createUser', createUser),
  path('deleteUser/<int:userid>/', deleteUser),
  path('authorize/', StripeAuthorizeView.as_view(), name='authorize'),
  path('oauth/callback/', StripeAuthorizeCallbackView.as_view(), name='authorize_callback'),
  path('charge/', UserChargeView.as_view(), name='charge'),
  path('<int:pk>/', PersonDetailView.as_view(), name='person_detail'),

]
