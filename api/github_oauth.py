import requests
import urllib.parse
from django.conf import settings
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class GitHubOAuthService:
    """
    Service class to handle GitHub OAuth authentication flow
    """
    
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_API_URL = "https://api.github.com/user"
    GITHUB_USER_EMAILS_API_URL = "https://api.github.com/user/emails"

    @classmethod
    def get_authorization_url(cls, state: str = None) -> str:
        """
        Generate GitHub OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: GitHub authorization URL
        """
        params = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'redirect_uri': settings.GITHUB_REDIRECT_URI,
            'scope': 'user:email',  # Request email permissions
            'response_type': 'code'
        }
        
        if state:
            params['state'] = state
            
        query_string = urllib.parse.urlencode(params)
        return f"{cls.GITHUB_AUTH_URL}?{query_string}"

    @classmethod
    def exchange_code_for_token(cls, code: str) -> Optional[str]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from GitHub callback
            
        Returns:
            str: Access token if successful, None otherwise
        """
        try:
            data = {
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': settings.GITHUB_REDIRECT_URI,
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(cls.GITHUB_TOKEN_URL, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            
            if 'access_token' in token_data:
                return token_data['access_token']
            else:
                logger.error(f"No access token in response: {token_data}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token exchange: {e}")
            return None

    @classmethod
    def get_user_data(cls, access_token: str) -> Optional[Dict]:
        """
        Get user data from GitHub API using access token
        
        Args:
            access_token: GitHub access token
            
        Returns:
            dict: User data if successful, None otherwise
        """
        try:
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/json'
            }
            
            # Get user profile
            user_response = requests.get(cls.GITHUB_USER_API_URL, headers=headers, timeout=10)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get user emails
            emails_response = requests.get(cls.GITHUB_USER_EMAILS_API_URL, headers=headers, timeout=10)
            emails_response.raise_for_status()
            emails_data = emails_response.json()
            
            # Find primary email
            primary_email = None
            for email_info in emails_data:
                if email_info.get('primary', False):
                    primary_email = email_info.get('email')
                    break
            
            # If no primary email found, use the first verified email
            if not primary_email:
                for email_info in emails_data:
                    if email_info.get('verified', False):
                        primary_email = email_info.get('email')
                        break
            
            # If still no email found, use the first email
            if not primary_email and emails_data:
                primary_email = emails_data[0].get('email')
            
            # Combine user data
            combined_data = {
                'id': user_data.get('id'),
                'login': user_data.get('login'),
                'email': primary_email or user_data.get('email'),
                'name': user_data.get('name'),
                'avatar_url': user_data.get('avatar_url'),
                'bio': user_data.get('bio'),
                'company': user_data.get('company'),
                'location': user_data.get('location'),
                'public_repos': user_data.get('public_repos'),
                'followers': user_data.get('followers'),
                'following': user_data.get('following'),
                'created_at': user_data.get('created_at'),
                'updated_at': user_data.get('updated_at')
            }
            
            return combined_data
            
        except requests.RequestException as e:
            logger.error(f"Error getting user data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user data: {e}")
            return None

    @classmethod
    def parse_user_for_registration(cls, github_user_data: Dict) -> Dict:
        """
        Parse GitHub user data for user registration
        
        Args:
            github_user_data: Raw GitHub user data
            
        Returns:
            dict: Parsed data for user creation
        """
        # Split name into first and last name
        name = (github_user_data.get('name') or '').strip()
        first_name = ''
        last_name = ''
        
        if name:
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            if len(name_parts) > 1:
                last_name = name_parts[1]
        
        return {
            'email': github_user_data.get('email'),
            'first_name': first_name,
            'last_name': last_name,
            'github_id': str(github_user_data.get('id')),
            'github_username': github_user_data.get('login'),
            'github_avatar_url': github_user_data.get('avatar_url'),
            'is_github_user': True,
            'is_active': True
        } 