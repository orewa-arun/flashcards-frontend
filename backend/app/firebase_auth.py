import os
import json
import logging
import firebase_admin
from typing import Optional
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Credentials are loaded in the following order:
    1. FIREBASE_CREDENTIALS environment variable (JSON string) - for deployment
    2. GOOGLE_APPLICATION_CREDENTIALS environment variable (file path) - for local development
    3. Application Default Credentials - fallback for cloud environments
    
    Raises:
        HTTPException: If Firebase initialization fails
    """
    # Skip if already initialized
    if firebase_admin._apps:
        logger.info("Firebase Admin SDK already initialized")
        return
    
    # Method 1: Try environment variable with JSON credentials (deployment)
    firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS')
    if firebase_creds_json:
        try:
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized with FIREBASE_CREDENTIALS environment variable")
            return
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in FIREBASE_CREDENTIALS: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase with FIREBASE_CREDENTIALS: {e}")
    
    # Method 2: Try local file path (local development)
    service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if service_account_path:
        if os.path.exists(service_account_path):
            try:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info(f"✅ Firebase Admin SDK initialized with service account file: {service_account_path}")
                return
            except Exception as e:
                logger.error(f"❌ Failed to initialize Firebase with file {service_account_path}: {e}")
        else:
            logger.warning(f"⚠️ GOOGLE_APPLICATION_CREDENTIALS path does not exist: {service_account_path}")
    
    # Method 3: Try application default credentials (cloud environment fallback)
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized with Application Default Credentials")
        return
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase with Application Default Credentials: {e}")
    
    # If we reach here, all methods failed
    error_msg = (
        "Firebase Admin SDK initialization failed. "
        "Please set either FIREBASE_CREDENTIALS (JSON string) or "
        "GOOGLE_APPLICATION_CREDENTIALS (file path) environment variable."
    )
    logger.error(f"❌ {error_msg}")
    raise HTTPException(status_code=500, detail=error_msg)


# Security scheme for extracting Bearer tokens
# Use auto_error=False to allow manual handling of missing tokens (needed for debug mode bypass)
security = HTTPBearer(auto_error=False)

async def verify_firebase_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Verify Firebase ID token and return user information.
    
    Args:
        credentials: HTTP Authorization credentials containing the Bearer token
        
    Returns:
        dict: User information from Firebase token
        
    Raises:
        HTTPException: If token is invalid or verification fails
    """
    # DEBUG MODE BYPASS: If DEBUG is true, return a stub user immediately
    if settings.DEBUG:
        # logger.debug("🚧 DEBUG mode: Bypassing Firebase auth with dev-user")
        return {
            "uid": "dev-user",
            "email": "dev@example.com",
            "name": "Developer User",
            "picture": "",
            "email_verified": True,
            "firebase_claims": {"admin": True}
        }

    # NORMAL MODE: Require and verify token
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        
        user_info = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified', False),
            'firebase_claims': decoded_token
        }
        
        logger.debug(f"✅ Token verified for user: {user_info['uid']}")
        return user_info
        
    except auth.InvalidIdTokenError:
        logger.warning("⚠️ Invalid Firebase ID token")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except auth.ExpiredIdTokenError:
        logger.warning("⚠️ Expired Firebase ID token")
        raise HTTPException(status_code=401, detail="Authentication token has expired")
    except Exception as e:
        logger.error(f"❌ Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication verification failed")


async def get_current_user(user_info: dict = Depends(verify_firebase_token)):
    """
    Get current authenticated user information.
    
    Args:
        user_info: User information from Firebase token verification
        
    Returns:
        dict: Current user information
    """
    return user_info


async def get_admin_user(user_info: dict = Depends(verify_firebase_token)):
    """
    Verify that the current user has admin privileges.
    
    Args:
        user_info: User information from Firebase token verification
        
    Returns:
        dict: Admin user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    firebase_claims = user_info.get('firebase_claims', {})
    is_admin = firebase_claims.get('admin', False)
    
    if not is_admin:
        logger.warning(f"⚠️ Non-admin user {user_info['uid']} attempted to access admin endpoint")
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return user_info
