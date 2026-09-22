import os
import time
import secrets
import hashlib
import smtplib
from email.message import EmailMessage
import jwt
from fastapi import APIRouter, HTTPException, Depends, Query, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth")

# In-memory store: email -> { hash: str, expires_at: float, attempts: int }
_otp_store = {}

JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-default-key-for-dev")
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def _send_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"Your Fusion Engine login OTP is: {otp}\n\nIt expires in 5 minutes.")
    msg["Subject"] = "Fusion Engine OTP"
    msg["From"] = SMTP_USER or "noreply@fusion-engine.local"
    msg["To"] = to_email

    if not SMTP_SERVER:
        print("\n" + "="*50)
        print(f"DEV_MODE: No SMTP config found.")
        print(f"Intercepted email to {to_email}")
        print(f"OTP: {otp}")
        print("="*50 + "\n")
        return

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email.")

@router.post("/request-otp")
def request_otp(req: OTPRequest):
    email = req.email.strip().lower()
    otp = str(secrets.randbelow(1000000)).zfill(6)
    
    _otp_store[email] = {
        "hash": _hash_otp(otp),
        "expires_at": time.time() + 300, # 5 mins
        "attempts": 0
    }
    
    _send_email(email, otp)
    return {"message": "OTP sent."}

@router.post("/verify-otp")
def verify_otp(req: OTPVerify):
    email = req.email.strip().lower()
    record = _otp_store.get(email)
    
    if not record:
        raise HTTPException(status_code=400, detail="No OTP requested or expired.")
        
    if time.time() > record["expires_at"]:
        del _otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired.")
        
    record["attempts"] += 1
    if record["attempts"] > 3:
        del _otp_store[email]
        raise HTTPException(status_code=400, detail="Too many attempts. Request a new OTP.")
        
    if record["hash"] != _hash_otp(req.otp.strip()):
        raise HTTPException(status_code=400, detail="Invalid OTP.")
        
    # Success
    del _otp_store[email]
    
    token = jwt.encode({"sub": email, "exp": time.time() + 86400}, JWT_SECRET, algorithm="HS256")
    return {"token": token, "email": email}

def get_current_user_from_header(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    return _verify_token(token)

def get_current_user_from_query(token: Optional[str] = Query(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    return _verify_token(token)

def _verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
