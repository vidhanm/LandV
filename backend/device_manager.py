import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database import ActiveSession

class DeviceManager:
    """
    Manages device registration, session tracking, and N-device limit enforcement.
    Implements device fingerprinting and force logout functionality.
    """
    
    def __init__(self):
        self.max_devices = int(os.getenv("MAX_DEVICES", "2"))
        self.session_timeout_hours = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    def generate_device_id(self, user_agent: str, ip_address: str, additional_data: str = "") -> str:
        """
        Generate a unique device fingerprint based on user agent, IP, and additional data.
        
        Args:
            user_agent: Browser/device user agent string
            ip_address: Client IP address
            additional_data: Additional device-specific data (optional)
            
        Returns:
            str: Unique device identifier hash
        """
        # Combine device characteristics for fingerprinting
        device_string = f"{user_agent}|{ip_address}|{additional_data}"
        
        # Generate SHA-256 hash as device ID
        device_id = hashlib.sha256(device_string.encode()).hexdigest()
        
        return device_id
    
    def cleanup_expired_sessions(self, db: Session, user_id: str = None) -> int:
        """
        Remove expired sessions from the database.
        
        Args:
            db: Database session
            user_id: Optional user ID to cleanup specific user's sessions
            
        Returns:
            int: Number of sessions cleaned up
        """
        expiry_time = datetime.utcnow() - timedelta(hours=self.session_timeout_hours)
        
        query = db.query(ActiveSession).filter(ActiveSession.last_active < expiry_time)
        
        if user_id:
            query = query.filter(ActiveSession.user_id == user_id)
        
        expired_sessions = query.all()
        count = len(expired_sessions)
        
        # Delete expired sessions
        query.delete()
        db.commit()
        
        return count
    
    def get_user_sessions(self, db: Session, user_id: str) -> List[ActiveSession]:
        """
        Get all active sessions for a specific user.
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            
        Returns:
            List[ActiveSession]: List of active sessions
        """
        # Clean up expired sessions first
        self.cleanup_expired_sessions(db, user_id)
        
        sessions = db.query(ActiveSession)\
                    .filter(ActiveSession.user_id == user_id)\
                    .order_by(ActiveSession.last_active.desc())\
                    .all()
        
        return sessions
    
    def update_session_activity(self, db: Session, user_id: str, device_id: str) -> bool:
        """
        Update the last_active timestamp for a session (heartbeat).
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            device_id: Device identifier
            
        Returns:
            bool: True if session was updated, False if not found
        """
        session = db.query(ActiveSession)\
                   .filter(and_(
                       ActiveSession.user_id == user_id,
                       ActiveSession.device_id == device_id
                   ))\
                   .first()
        
        if session:
            session.last_active = datetime.utcnow()
            db.commit()
            return True
        
        return False
    
    def create_session(
        self,
        db: Session,
        user_id: str,
        device_id: str,
        user_agent: str,
        ip_address: str
    ) -> ActiveSession:
        """
        Create a new session for a device.
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            device_id: Device identifier
            user_agent: Browser/device user agent
            ip_address: Client IP address
            
        Returns:
            ActiveSession: Created session object
        """
        # Check if session already exists for this device
        existing_session = db.query(ActiveSession)\
                            .filter(and_(
                                ActiveSession.user_id == user_id,
                                ActiveSession.device_id == device_id
                            ))\
                            .first()
        
        if existing_session:
            # Update existing session
            existing_session.last_active = datetime.utcnow()
            existing_session.user_agent = user_agent
            existing_session.ip_address = ip_address
            db.commit()
            return existing_session
        
        # Create new session
        new_session = ActiveSession(
            user_id=user_id,
            device_id=device_id,
            user_agent=user_agent,
            ip_address=ip_address,
            login_time=datetime.utcnow(),
            last_active=datetime.utcnow()
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session
    
    def remove_session(self, db: Session, user_id: str, device_id: str) -> bool:
        """
        Remove a specific session.
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            device_id: Device identifier
            
        Returns:
            bool: True if session was removed, False if not found
        """
        session = db.query(ActiveSession)\
                   .filter(and_(
                       ActiveSession.user_id == user_id,
                       ActiveSession.device_id == device_id
                   ))\
                   .first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        
        return False
    
    def get_oldest_session(self, db: Session, user_id: str) -> Optional[ActiveSession]:
        """
        Get the oldest (least recently active) session for a user.
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            
        Returns:
            Optional[ActiveSession]: Oldest session or None if no sessions
        """
        session = db.query(ActiveSession)\
                   .filter(ActiveSession.user_id == user_id)\
                   .order_by(ActiveSession.last_active.asc())\
                   .first()
        
        return session
    
    async def register_device(
        self,
        db: Session,
        user_id: str,
        user_agent: str,
        ip_address: str,
        additional_data: str = ""
    ) -> Dict:
        """
        Register a new device, handling N-device limit enforcement.
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            user_agent: Browser/device user agent
            ip_address: Client IP address
            additional_data: Additional device-specific data
            
        Returns:
            Dict: Registration result with success status and any conflicts
        """
        # Generate device fingerprint
        device_id = self.generate_device_id(user_agent, ip_address, additional_data)
        
        # Clean up expired sessions
        self.cleanup_expired_sessions(db, user_id)
        
        # Check if this device is already registered
        existing_session = db.query(ActiveSession)\
                            .filter(and_(
                                ActiveSession.user_id == user_id,
                                ActiveSession.device_id == device_id
                            ))\
                            .first()
        
        if existing_session:
            # Update existing session activity
            existing_session.last_active = datetime.utcnow()
            existing_session.user_agent = user_agent
            existing_session.ip_address = ip_address
            db.commit()
            
            return {
                "success": True,
                "message": "Device session updated",
                "device_id": device_id,
                "conflict": False
            }
        
        # Get current active sessions
        current_sessions = self.get_user_sessions(db, user_id)
        
        # Check if we're at the device limit
        if len(current_sessions) >= self.max_devices:
            # Return conflict information
            return {
                "success": False,
                "message": f"Device limit reached ({self.max_devices} devices maximum)",
                "device_id": device_id,
                "conflict": True,
                "current_sessions": [session.to_dict() for session in current_sessions],
                "max_devices": self.max_devices
            }
        
        # Create new session
        new_session = self.create_session(db, user_id, device_id, user_agent, ip_address)
        
        return {
            "success": True,
            "message": "Device registered successfully",
            "device_id": device_id,
            "conflict": False,
            "session": new_session.to_dict()
        }
    
    async def force_logout_and_register(
        self,
        db: Session,
        user_id: str,
        device_id_to_logout: str,
        new_user_agent: str,
        new_ip_address: str,
        additional_data: str = ""
    ) -> Dict:
        """
        Force logout a specific device and register the new device.
        
        Args:
            db: Database session
            user_id: Auth0 user ID
            device_id_to_logout: Device ID to force logout
            new_user_agent: New device user agent
            new_ip_address: New device IP address
            additional_data: Additional device-specific data
            
        Returns:
            Dict: Force logout and registration result
        """
        # Remove the specified session
        removed = self.remove_session(db, user_id, device_id_to_logout)
        
        if not removed:
            return {
                "success": False,
                "message": "Device to logout not found",
                "device_logged_out": device_id_to_logout
            }
        
        # Generate device ID for new device
        new_device_id = self.generate_device_id(new_user_agent, new_ip_address, additional_data)
        
        # Create session for new device
        new_session = self.create_session(db, user_id, new_device_id, new_user_agent, new_ip_address)
        
        return {
            "success": True,
            "message": "Device logged out and new device registered",
            "device_logged_out": device_id_to_logout,
            "new_device_id": new_device_id,
            "new_session": new_session.to_dict()
        }
    
    def get_session_statistics(self, db: Session, user_id: str = None) -> Dict:
        """
        Get session statistics for monitoring and debugging.
        
        Args:
            db: Database session
            user_id: Optional user ID for user-specific stats
            
        Returns:
            Dict: Session statistics
        """
        query = db.query(ActiveSession)
        
        if user_id:
            query = query.filter(ActiveSession.user_id == user_id)
        
        total_sessions = query.count()
        
        # Get session count by user
        user_session_counts = db.query(
            ActiveSession.user_id,
            func.count(ActiveSession.id).label('session_count')
        ).group_by(ActiveSession.user_id).all()
        
        # Find users exceeding device limit
        users_over_limit = [
            {"user_id": user_id, "session_count": count}
            for user_id, count in user_session_counts
            if count > self.max_devices
        ]
        
        stats = {
            "total_active_sessions": total_sessions,
            "max_devices_allowed": self.max_devices,
            "session_timeout_hours": self.session_timeout_hours,
            "users_over_limit": users_over_limit
        }
        
        if user_id:
            user_sessions = self.get_user_sessions(db, user_id)
            stats["user_session_count"] = len(user_sessions)
            stats["user_sessions"] = [session.to_dict() for session in user_sessions]
        
        return stats