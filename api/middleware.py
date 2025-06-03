from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class JWTCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        logger.debug(f"Processing request: {request.path}")
        logger.debug(f"Cookies: {request.COOKIES}")
        
        access_token = request.COOKIES.get('access_token')
        logger.debug(f"Access token: {access_token}")
        
        if access_token:
            try:
                # Create a new request with the token in the Authorization header
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
                
                # Try to authenticate using JWT authentication
                auth_tuple = self.jwt_auth.authenticate(request)
                if auth_tuple is not None:
                    request.user, request.auth = auth_tuple
                    logger.debug(f"User authenticated via JWT: {request.user.email}")
                else:
                    request.user = AnonymousUser()
                    request.auth = None
            except Exception as e:
                logger.error(f"Error processing token: {str(e)}")
                request.user = AnonymousUser()
                request.auth = None
        else:
            logger.debug("No access token found in cookies")
            request.user = AnonymousUser()
            request.auth = None
            
        logger.debug(f"Final user: {request.user}")
        logger.debug(f"Final auth: {request.auth}")
        return self.get_response(request) 