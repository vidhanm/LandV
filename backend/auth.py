from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
import requests
from typing import Dict, Optional
from functools import lru_cache
import time

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_IDENTIFIER = os.getenv("AUTH0_API_IDENTIFIER")
AUTH0_ALGORITHMS = ["RS256"]

security = HTTPBearer()

class Auth0JWKSClient:
    """
    Client for fetching and caching Auth0 JWKS (JSON Web Key Set).
    Handles public key retrieval for JWT token validation.
    """
    
    def __init__(self, domain: str):
        self.domain = domain
        self.jwks_uri = f"https://{domain}/.well-known/jwks.json"
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    @lru_cache(maxsize=10)
    def get_jwks(self) -> Dict:
        """Fetch JWKS from Auth0 with caching"""
        try:
            response = requests.get(self.jwks_uri, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch JWKS from Auth0: {str(e)}"
            )
    
    def get_signing_key(self, kid: str) -> str:
        """
        Get the signing key for a specific key ID from JWKS.
        Used for validating JWT tokens signed by Auth0.
        """
        # Check cache first
        if kid in self._cache:
            if time.time() - self._cache_time[kid] < self._cache_ttl:
                return self._cache[kid]
        
        jwks = self.get_jwks()
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Construct the RSA key
                if key.get("kty") == "RSA":
                    # Cache the key
                    self._cache[kid] = key
                    self._cache_time[kid] = time.time()
                    return key
        
        raise HTTPException(
            status_code=401,
            detail=f"Unable to find signing key with kid: {kid}"
        )

# Initialize JWKS client
jwks_client = Auth0JWKSClient(AUTH0_DOMAIN) if AUTH0_DOMAIN else None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Verify Auth0 JWT token and return decoded payload.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        Dict: Decoded JWT payload containing user information
        
    Raises:
        HTTPException: If token is invalid or verification fails
    """
    if not AUTH0_DOMAIN or not AUTH0_API_IDENTIFIER:
        raise HTTPException(
            status_code=500,
            detail="Auth0 configuration missing. Please set AUTH0_DOMAIN and AUTH0_API_IDENTIFIER."
        )
    
    token = credentials.credentials
    
    try:
        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=401,
                detail="Token missing key ID in header"
            )
        
        # Get signing key from JWKS
        signing_key = jwks_client.get_signing_key(kid)
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_API_IDENTIFIER,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token validation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}"
        )

def get_current_user(token_payload: Dict = Depends(verify_token)) -> Dict:
    """
    Extract current user information from verified JWT token.
    
    Args:
        token_payload: Verified JWT payload from verify_token
        
    Returns:
        Dict: User information including ID, email, name, etc.
    """
    # Validate required fields
    if not token_payload.get("sub"):
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID (sub claim)"
        )
    
    # Extract user information from token
    user_info = {
        "sub": token_payload.get("sub"),  # Auth0 user ID
        "email": token_payload.get("email"),
        "email_verified": token_payload.get("email_verified", False),
        "name": token_payload.get("name"),
        "nickname": token_payload.get("nickname"),
        "picture": token_payload.get("picture"),
        "phone_number": token_payload.get("phone_number"),
        "phone": token_payload.get("phone"),  # Alternative phone field
        "updated_at": token_payload.get("updated_at"),
        "iss": token_payload.get("iss"),
        "aud": token_payload.get("aud"),
        "iat": token_payload.get("iat"),
        "exp": token_payload.get("exp"),
    }
    
    # Remove None values
    user_info = {k: v for k, v in user_info.items() if v is not None}
    
    return user_info

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """
    Get current user information if token is provided, otherwise return None.
    Useful for endpoints that work both with and without authentication.
    
    Args:
        credentials: Optional bearer token from Authorization header
        
    Returns:
        Optional[Dict]: User information if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token_payload = verify_token(credentials)
        return get_current_user(token_payload)
    except HTTPException:
        return None

# Middleware for Auth0 token validation
async def auth_middleware(request: Request, call_next):
    """
    Optional middleware to validate Auth0 tokens on all requests.
    Can be used to automatically validate tokens across the application.
    """
    # Skip auth for certain paths
    skip_paths = ["/", "/docs", "/redoc", "/openapi.json", "/health"]
    
    if request.url.path in skip_paths:
        return await call_next(request)
    
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            verify_token(credentials)
        except HTTPException as e:
            # Could log the error or handle differently based on requirements
            pass
    
    return await call_next(request)

# Utility functions for token management
def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token without full validation.
    Useful for WebSocket connections where we need quick user ID extraction.
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[str]: User ID if found, None otherwise
    """
    try:
        # Decode without verification (only for user ID extraction)
        payload = jwt.get_unverified_claims(token)
        return payload.get("sub")
    except:
        return None

def is_token_expired(token: str) -> bool:
    """
    Check if JWT token is expired without full validation.
    
    Args:
        token: JWT token string
        
    Returns:
        bool: True if token is expired, False otherwise
    """
    try:
        payload = jwt.get_unverified_claims(token)
        exp = payload.get("exp")
        if exp:
            return time.time() > exp
        return True
    except:
        return True