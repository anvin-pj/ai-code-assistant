
import os
import httpx # 🚀 Step 1: Import httpx explicitly
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt
import bcrypt
from dotenv import load_dotenv

from supabase import create_client, Client

# --- 🚀 ENVIRONMENT VARIABLE INGESTION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
for _ in range(4):
    test_path = os.path.join(current_dir, ".env")
    if os.path.exists(test_path):
        load_dotenv(dotenv_path=test_path)
        break
    current_dir = os.path.dirname(current_dir)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("🔴 CONFIGURATION ERROR: Keys are unassigned inside your active .env template!")


# --- 🔓 CORPORATE FIREWALL BYPASS ENHANCEMENT ---
# We create a custom HTTP client and explicitly tell it to skip SSL certificate verification
custom_http_client = httpx.Client(verify=False)

# Import ClientOptions directly from supabase.client
from supabase.client import ClientOptions

# 🚀 FIXED: Changed parameter name from http_client to httpx_client
supabase_api: Client = create_client(
    supabase_url=SUPABASE_URL, 
    supabase_key=SUPABASE_KEY,
    options=ClientOptions(
        httpx_client=custom_http_client
    )
)
print("📡 SUCCESS: Network-proof Supabase API client active on Port 443.")



# --- JWT Configuration ---
SECRET_KEY = "SUPER_SECRET_PIZZA_KEY_CHANGE_THIS_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="Firewall-Proof Supabase API Authentication Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignUpModel(BaseModel):
    username: str
    password: str

# --- Operational API Routes ---

@app.post("/auth/signup")
def signup(user: SignUpModel):
    username_cleaned = user.username.strip()
    
    # 🕵️‍♂️ Check for existing users using Web API queries
    try:
        existing = supabase_api.table("users").select("username").eq("username", username_cleaned).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Username registration conflict: Handle already exists.")
    except Exception as api_err:
        raise HTTPException(status_code=500, detail=f"Database schema missing. Make sure your 'users' table is built in Supabase: {api_err}")

    # Hash the password string
    password_bytes = user.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    hashed_string = hashed_bytes.decode('utf-8')
    
    # 🚀 Insert straight into the cloud table over Web HTTP traffic
    supabase_api.table("users").insert({
        "username": username_cleaned,
        "hashed_password": hashed_string
    }).execute()
    
    return {"status": "success", "message": f"Account '{username_cleaned}' created in Supabase!"}

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    input_username = str(form_data.username).strip()
    input_password = form_data.password
    
    # Fetch user records from cloud
    user_query = supabase_api.table("users").select("*").eq("username", input_username).execute()
    if not user_query.data:
        raise HTTPException(status_code=401, detail="Incorrect username or password configuration.")
    
    db_user = user_query.data[0]
    
    password_bytes = input_password.encode('utf-8')
    db_hash_bytes = db_user["hashed_password"].encode('utf-8')
    
    if not bcrypt.checkpw(password_bytes, db_hash_bytes):
        raise HTTPException(status_code=401, detail="Incorrect username or password configuration.")
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(db_user["username"]), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}