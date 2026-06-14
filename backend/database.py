import os
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Exclusively check for Supabase credentials
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase credentials missing! Please configure SUPABASE_URL and SUPABASE_KEY in your .env file."
    )

# Initialize Supabase client
try:
    supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase database client initialized successfully via HTTP API.")
except Exception as e:
    raise RuntimeError(f"Error initializing Supabase client: {e}")

def create_tables():
    # Inform the developer of table requirements in Supabase dashboard
    print("Using Supabase. Please ensure 'predictions' and 'users' tables exist in your Supabase project.")

# --- User Authentication Functions ---

def register_user(email, password):
    hashed = generate_password_hash(password)
    try:
        # Check if user already exists in Supabase
        res = supabase_client.table("users").select("*").eq("email", email).execute()
        if len(res.data) > 0:
            return False, "Email already registered."
            
        # Insert new user into Supabase
        supabase_client.table("users").insert({
            "email": email,
            "password": hashed
        }).execute()
        return True, "User registered successfully."
    except Exception as e:
        err_msg = str(e)
        if "row-level security" in err_msg.lower() or "42501" in err_msg:
            return False, "Database permission error: Row Level Security (RLS) is enabled on 'users' table in Supabase. Please disable RLS or use a Service Role key."
        return False, f"Supabase auth error: {err_msg}"

def authenticate_user(email, password):
    try:
        # Retrieve user record from Supabase
        res = supabase_client.table("users").select("*").eq("email", email).execute()
        if len(res.data) == 0:
            return False, "Invalid email or password."
            
        user_record = res.data[0]
        if check_password_hash(user_record["password"], password):
            return True, "Authentication successful."
        return False, "Invalid email or password."
    except Exception as e:
        err_msg = str(e)
        if "row-level security" in err_msg.lower() or "42501" in err_msg:
            return False, "Database permission error: Row Level Security (RLS) is enabled on 'users' table in Supabase. Please disable RLS or use a Service Role key."
        return False, f"Supabase login failure: {err_msg}"

# --- Prediction Logs Functions ---

def log_prediction(user_email, chasing_team, defending_team, target_score, current_score, wickets_lost, 
                   balls_left, chasing_probability, defending_probability, predicted_winner):
    data = {
        "chasing_team": chasing_team,
        "defending_team": defending_team,
        "target_score": int(target_score),
        "current_score": int(current_score),
        "wickets_lost": int(wickets_lost),
        "balls_left": int(balls_left),
        "chasing_probability": float(chasing_probability),
        "defending_probability": float(defending_probability),
        "predicted_winner": predicted_winner
    }
    
    # Try logging with user_email first
    try:
        data_with_user = data.copy()
        data_with_user["user_email"] = user_email
        supabase_client.table("predictions").insert(data_with_user).execute()
        print("Prediction logged to Supabase history table with user_email.")
        return
    except Exception as e:
        print(f"Failed to log with user_email (might be missing column): {e}")

    # Fallback without user_email
    try:
        supabase_client.table("predictions").insert(data).execute()
        print("Prediction logged to Supabase history table (fallback without user_email).")
    except Exception as e:
        err_msg = str(e)
        if "row-level security" in err_msg.lower() or "42501" in err_msg:
            print("Failed to log prediction to Supabase: Row Level Security (RLS) is enabled on 'predictions' table. Please disable RLS or use a Service Role key.")
        else:
            print(f"Failed to log prediction to Supabase: {err_msg}")

def get_predictions_history(user_email=None, limit=50):
    try:
        # Build query for predictions
        query = supabase_client.table("predictions").select("*")
        
        # Filter by user_email if provided
        if user_email:
            query = query.eq("user_email", user_email)
            
        response = query.order("created_at", desc=True).limit(limit).execute()
        history = []
        for row in response.data:
            history.append({
                "id": row["id"],
                "chasing_team": row["chasing_team"],
                "defending_team": row["defending_team"],
                "target_score": row["target_score"],
                "current_score": row["current_score"],
                "wickets_lost": row["wickets_lost"],
                "balls_left": row["balls_left"],
                "chasing_win_probability": row["chasing_probability"],
                "defending_win_probability": row["defending_probability"],
                "predicted_winner": row["predicted_winner"],
                "created_at": row["created_at"]
            })
        return history
    except Exception as e:
        print(f"Failed to query history from Supabase: {e}")
        return []

if __name__ == "__main__":
    create_tables()
