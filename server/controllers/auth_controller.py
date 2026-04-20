import os
from utility.security import create_jwt_token, verify_jwt_token


class AuthController:
    """Controller for admin authentication"""
    
    def __init__(self):
        # Load admin password from environment variable (fallback to default)
        self.admin_password = os.getenv("ADMIN_PASSWORD", "SuperSecureAdminPassword123!")
    
    async def login(self, password: str) -> dict:
        """
        Authenticate admin and return JWT token
        
        Args:
            password: The admin password
            
        Returns:
            dict with token and expiration info
            
        Raises:
            ValueError if password is incorrect
        """
        if password != self.admin_password:
            raise ValueError("Invalid password")
        
        token = create_jwt_token(admin_id="admin")
        return {
            "token": token,
            "token_type": "bearer",
            "expires_in_minutes": 15,
            "message": "Login successful"
        }


# Create singleton instance
auth_controller = AuthController()
