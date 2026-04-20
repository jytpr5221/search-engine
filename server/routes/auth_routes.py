from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from controllers.auth_controller import auth_controller

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
async def admin_login(login_request: LoginRequest):
    """
    Admin login endpoint - accepts only password
    Returns JWT token valid for 15 minutes
    """
    try:
        result = await auth_controller.login(login_request.password)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )
