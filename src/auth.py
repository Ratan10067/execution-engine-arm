"""
Authentication and Authorization middleware for Judge0 Engine.
Supports X-Auth-Token, X-Auth-User, and RapidAPI authentication headers.
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from src.config import settings


def verify_auth(request: Request):
    """
    Verify request authentication headers if configured in settings.
    """
    # 1. RapidAPI check if configured
    if settings.RAPIDAPI_KEY:
        rapid_key = request.headers.get("X-RapidAPI-Key") or request.headers.get("x-rapidapi-key")
        if not rapid_key or rapid_key != settings.RAPIDAPI_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing RapidAPI Key",
            )

    # 2. Authentication token check if configured
    if settings.AUTHN_TOKEN:
        header_name = settings.AUTHN_HEADER
        token_val = request.headers.get(header_name) or request.headers.get(header_name.lower())
        if not token_val or token_val != settings.AUTHN_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid or missing authentication token",
            )

    # 3. Authorization token check if configured
    if settings.AUTHZ_TOKEN:
        authz_header = settings.AUTHZ_HEADER
        authz_val = request.headers.get(authz_header) or request.headers.get(authz_header.lower())
        if not authz_val or authz_val != settings.AUTHZ_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Invalid or missing authorization user token",
            )
