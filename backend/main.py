from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import uvicorn

from database import get_db, create_tables
from auth import verify_token, get_current_user
from device_manager import DeviceManager
from websockets import connection_manager, handle_websocket_message

load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Multi-Device Authentication API",
    description="FastAPI backend for managing multi-device authentication with Auth0 integration",
    version="1.0.0"
)

# CORS configuration for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://*.vercel.app",   # Vercel deployments
        os.getenv("FRONTEND_URL", "")  # Production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
device_manager = DeviceManager()

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    create_tables()
    print("✅ Database tables initialized")
    print("✅ Multi-Device Authentication API started")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "Multi-Device Authentication API",
        "status": "active",
        "max_devices": int(os.getenv("MAX_DEVICES", "2"))
    }

@app.post("/auth/validate-token")
async def validate_token(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Validate Auth0 JWT token and return user information.
    This endpoint verifies the token and extracts user details.
    """
    try:
        return {
            "valid": True,
            "user": current_user,
            "message": "Token is valid"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")

@app.get("/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile information from Auth0 token.
    Returns user details like name, email, phone number.
    """
    return {
        "user_id": current_user.get("sub"),
        "name": current_user.get("name"),
        "email": current_user.get("email"),
        "phone": current_user.get("phone_number", current_user.get("phone")),
        "picture": current_user.get("picture")
    }

@app.post("/device/register")
async def register_device(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new device for the current user.
    Handles N-device limit enforcement and returns conflict information if needed.
    """
    try:
        # Extract device information from request
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host
        user_id = current_user.get("sub")
        
        # Attempt to register the device
        result = await device_manager.register_device(
            db=db,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device registration failed: {str(e)}")

@app.get("/device/sessions")
async def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all active sessions for the current user.
    Returns list of devices with session information.
    """
    user_id = current_user.get("sub")
    sessions = device_manager.get_user_sessions(db, user_id)
    
    return {
        "user_id": user_id,
        "active_sessions": [session.to_dict() for session in sessions],
        "session_count": len(sessions)
    }

@app.post("/device/force-logout")
async def force_logout_device(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Force logout a specific device and register the current device.
    Used when user chooses to logout previous device from conflict modal.
    """
    try:
        body = await request.json()
        device_id_to_logout = body.get("device_id")
        
        if not device_id_to_logout:
            raise HTTPException(status_code=400, detail="device_id is required")
        
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host
        user_id = current_user.get("sub")
        
        # Force logout the specified device and register current device
        result = await device_manager.force_logout_and_register(
            db=db,
            user_id=user_id,
            device_id_to_logout=device_id_to_logout,
            new_user_agent=user_agent,
            new_ip_address=ip_address
        )
        
        # Send WebSocket notification to the logged-out device
        await connection_manager.send_logout_notification(
            user_id=user_id,
            device_id=device_id_to_logout,
            reason="force_logout"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Force logout failed: {str(e)}")

@app.delete("/device/logout")
async def logout_current_device(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Logout the current device (normal logout).
    Removes the current device session from database.
    """
    try:
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host
        user_id = current_user.get("sub")
        
        # Generate device ID for current device
        device_id = device_manager.generate_device_id(user_agent, ip_address)
        
        # Remove the session
        result = device_manager.remove_session(db, user_id, device_id)
        
        return {"message": "Logged out successfully", "device_id": device_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time notifications.
    Handles logout notifications and device conflict alerts.
    """
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            await handle_websocket_message(websocket, data, user_id)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for better error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )