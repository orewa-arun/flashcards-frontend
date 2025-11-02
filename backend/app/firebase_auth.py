import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    try:
        # Check if Firebase is already initialized
        if not firebase_admin._apps:
            # Get the path to service account key from environment variable
            service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            if service_account_path and os.path.exists(service_account_path):
                # Initialize with service account file
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully with service account file")
            else:
                # Try to initialize with default credentials (for production environments)
                try:
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized with default credentials")
                except Exception as e:
                    logger.error(f"Failed to initialize Firebase with default credentials: {e}")
                    raise HTTPException(
                        status_code=500, 
                        detail="Firebase authentication not properly configured"
                    )
        else:
            logger.info("Firebase Admin SDK already initialized")
            
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Firebase authentication service unavailable"
        )

# Security scheme for extracting Bearer tokens
security = HTTPBearer()

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify Firebase ID token and return user information
    
    Args:
        credentials: HTTP Authorization credentials containing the Bearer token
        
    Returns:
        dict: User information from Firebase token
        
    Raises:
        HTTPException: If token is invalid or verification fails
    """
    try:
        # Extract the token from the Authorization header
        token = credentials.credentials
        
        # Verify the token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        
        # Extract user information
        user_info = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified', False),
            'firebase_claims': decoded_token
        }
        
        logger.info(f"Successfully verified token for user: {user_info['uid']}")
        return user_info
        
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase ID token provided")
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication verification failed"
        )

async def get_current_user(user_info: dict = Depends(verify_firebase_token)):
    """
    Get current authenticated user information
    
    Args:
        user_info: User information from Firebase token verification
        
    Returns:
        dict: Current user information
    """
    return user_info

# Optional: Create a dependency for admin users (if you need admin-only endpoints)
async def get_admin_user(user_info: dict = Depends(verify_firebase_token)):
    """
    Verify that the current user has admin privileges
    
    Args:
        user_info: User information from Firebase token verification
        
    Returns:
        dict: Admin user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Check if user has admin custom claims
    firebase_claims = user_info.get('firebase_claims', {})
    is_admin = firebase_claims.get('admin', False)
    
    if not is_admin:
        logger.warning(f"Non-admin user {user_info['uid']} attempted to access admin endpoint")
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return user_info
