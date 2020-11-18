from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
import base64
import binascii
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.permissions import BasePermission
from user.models import Person;
import hashlib


class FoodDiaryAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Get the username and password
        """
                Returns a `User` if a correct username and password have been supplied
                using HTTP Basic authentication.  Otherwise returns `None`.
                """
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'basic':

            try:
                email = request.session["email"]
                password = request.session["password"]
                person = Person.objects.get(email=email, pwd=password)
                request.user = person
                request.user.is_authenticated = True
            except:
                raise exceptions.AuthenticationFailed("Authentication Failed")
        else:
            try:
                try:
                    auth_decoded = base64.b64decode(auth[1]).decode('utf-8')
                except UnicodeDecodeError:
                    auth_decoded = base64.b64decode(auth[1]).decode('latin-1')
                auth_parts = auth_decoded.partition(':')
            except (TypeError, UnicodeDecodeError, binascii.Error):
                raise exceptions.AuthenticationFailed("Authentication Failed")

            email, password = auth_parts[0], auth_parts[2]
            try:
                person = Person.objects.get(email=email, pwd=hashlib.md5(password.encode('utf-8')).hexdigest())
                request.session['email'] = person.email
                request.session['password'] = person.pwd
                request.session['user_id'] = person.id
                request.session['authenticated'] = True
                role = "";
                if person.is_user == 1 and person.is_coach == 0:
                    role = "client";
                if person.is_user == 0 and person.is_coach == 1:
                    role = "coach";
                if person.is_user == 1 and person.is_coach == 1:
                    role = "admin";
                request.session['role'] = role

            except:
                raise exceptions.AuthenticationFailed("Authentication Failed")




        if person is None:
            raise exceptions.AuthenticationFailed('Invalid username/password.')


def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, str):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        try:
            return request.session['authenticated']
        except:
            return  False

