import jwt
import time
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AppleOAuthService:
    @staticmethod
    def generate_client_secret():
        """Generate a client secret for Apple Sign In"""
        try:
            # Get the current time
            now = int(time.time())
            
            # Create the JWT header
            headers = {
                'kid': settings.APPLE_KEY_ID,
                'alg': 'ES256'
            }
            
            # Create the JWT payload
            payload = {
                'iss': settings.APPLE_TEAM_ID,
                'iat': now,
                'exp': now + 15777000,  # 6 months
                'aud': 'https://appleid.apple.com',
                'sub': settings.APPLE_CLIENT_ID
            }
            
            # Sign the JWT with the private key
            client_secret = jwt.encode(
                payload,
                settings.APPLE_PRIVATE_KEY,
                algorithm='ES256',
                headers=headers
            )
            
            return client_secret
            
        except Exception as e:
            logger.error(f"Error generating Apple client secret: {e}")
            return None

    @staticmethod
    def get_authorization_url(state=None):
        """Get the Apple authorization URL"""
        try:
            base_url = 'https://appleid.apple.com/auth/authorize'
            params = {
                'response_type': 'code id_token',
                'client_id': settings.APPLE_CLIENT_ID,
                'redirect_uri': settings.APPLE_REDIRECT_URI,
                'state': state,
                'scope': 'name email',
                'response_mode': 'form_post'
            }
            
            # Build the URL with parameters
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            return url
            
        except Exception as e:
            logger.error(f"Error getting Apple authorization URL: {e}")
            return None

    @staticmethod
    def exchange_code_for_token(code):
        """Exchange authorization code for access token"""
        try:
            # Generate client secret
            client_secret = AppleOAuthService.generate_client_secret()
            if not client_secret:
                return None
            
            # Prepare the token request
            token_url = 'https://appleid.apple.com/auth/token'
            data = {
                'client_id': settings.APPLE_CLIENT_ID,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings.APPLE_REDIRECT_URI
            }
            
            # Make the request
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error exchanging code for token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging Apple code for token: {e}")
            return None

    @staticmethod
    def get_user_data(id_token):
        """Get user data from ID token"""
        try:
            # Decode the ID token
            decoded = jwt.decode(
                id_token,
                options={"verify_signature": False}
            )
            
            # Extract user data
            user_data = {
                'apple_id': decoded.get('sub'),
                'email': decoded.get('email'),
                'is_private_email': decoded.get('is_private_email', False),
                'email_verified': decoded.get('email_verified', False)
            }
            
            # If name is provided in the token
            if 'name' in decoded:
                user_data.update({
                    'first_name': decoded['name'].get('firstName', ''),
                    'last_name': decoded['name'].get('lastName', '')
                })
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting Apple user data: {e}")
            return None

    @staticmethod
    def parse_user_for_registration(user_data):
        """Parse user data for registration"""
        return {
            'email': user_data['email'],
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'apple_id': user_data['apple_id'],
            'is_apple_user': True,
            'is_active': True
        } 