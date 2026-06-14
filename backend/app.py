from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import pandas as pd
import math
import sys
import os

# Aligns path resolution using Pathlib
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "backend"))

from database import (
    create_tables, log_prediction, get_predictions_history,
    register_user, authenticate_user
)
from prediction_service import PredictionService

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

# Create database tables if they do not exist
create_tables()

# Initialize ML Prediction Service
predictor = PredictionService()

# Helper function to recursively clean NaN floats in dict lists to None (JSON null)
def clean_nan_to_none(records):
    for r in records:
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                r[k] = None
    return records

# --- Serving HTML Pages ---
@app.route("/")
def home():
    return send_from_directory("../frontend", "index.html")

@app.route("/login")
def login_page():
    from flask import redirect
    return redirect("/")

@app.route("/predictor")
def predictor_page():
    return send_from_directory("../frontend", "predictor.html")

@app.route("/dashboard")
def dashboard_page():
    return send_from_directory("../frontend", "dashboard.html")

@app.route("/players")
def players_page():
    return send_from_directory("../frontend", "players.html")

@app.route("/seasons")
def seasons_page():
    return send_from_directory("../frontend", "seasons.html")


# --- REST API Endpoints ---
@app.route("/api/auth/signup", methods=["POST"])
def auth_signup():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
            
        success, message = register_user(email, password)
        if success:
            return jsonify({
                "message": message,
                "user": email
            }), 201
        else:
            return jsonify({"error": message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
            
        success, message = authenticate_user(email, password)
        if success:
            return jsonify({
                "message": message,
                "user": email
            }), 200
        else:
            return jsonify({"error": message}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON inputs provided"}), 400

        user_email = data.get("user_email")
        chasing_team = data.get("chasing_team")
        defending_team = data.get("defending_team")
        target_score = data.get("target_score")
        current_score = data.get("current_score")
        completed_overs = data.get("completed_overs")
        current_over_balls = data.get("current_over_balls")
        wickets_lost = data.get("wickets_lost")

        # Validate inputs
        if any(v is None for v in [chasing_team, defending_team, target_score, current_score, completed_overs, current_over_balls, wickets_lost]):
            return jsonify({"error": "All fields are required"}), 400

        if str(chasing_team).strip().lower() == str(defending_team).strip().lower():
            return jsonify({"error": "Chasing team and defending team cannot be same"}), 400

        try:
            target_score = int(target_score)
            current_score = int(current_score)
            completed_overs = int(completed_overs)
            current_over_balls = int(current_over_balls)
            wickets_lost = int(wickets_lost)
        except ValueError:
            return jsonify({"error": "Numeric inputs must be valid integers"}), 400

        if target_score <= 0:
            return jsonify({"error": "Target score must be positive"}), 400

        if current_score < 0:
            return jsonify({"error": "Current score cannot be negative"}), 400

        if completed_overs < 0 or completed_overs > 19:
            return jsonify({"error": "Completed overs must be between 0 and 19"}), 400

        if current_over_balls < 0 or current_over_balls > 5:
            return jsonify({"error": "Current over balls must be between 0 and 5"}), 400

        if wickets_lost < 0 or wickets_lost > 10:
            return jsonify({"error": "Wickets lost must be between 0 and 10"}), 400

        # Calculate backend features
        balls_bowled = completed_overs * 6 + current_over_balls
        balls_left = 120 - balls_bowled

        if balls_left < 0:
            return jsonify({"error": "Balls left cannot be less than 0"}), 400

        # Generate ML model win probability
        result = predictor.predict(
            chasing_team=chasing_team,
            defending_team=defending_team,
            target_score=target_score,
            current_score=current_score,
            completed_overs=completed_overs,
            current_over_balls=current_over_balls,
            wickets_lost=wickets_lost
        )

        if "error" in result:
            return jsonify({"error": result["error"]}), 400

        # Save to predictions table
        log_prediction(
            user_email=user_email,
            chasing_team=chasing_team,
            defending_team=defending_team,
            target_score=target_score,
            current_score=current_score,
            wickets_lost=wickets_lost,
            balls_left=result["balls_left"],
            chasing_probability=result["chasing_win_probability"],
            defending_probability=result["defending_win_probability"],
            predicted_winner=result["predicted_winner"]
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/players", methods=["GET"])
def get_players():
    try:
        players_csv = BASE_DIR / "dataset" / "raw" / "players.csv"
        if not players_csv.exists():
            return jsonify({"error": "players.csv file is missing"}), 404
        
        # Read from raw player file
        df = pd.read_csv(players_csv)
        records = df.to_dict(orient="records")
        cleaned_records = clean_nan_to_none(records)
        return jsonify(cleaned_records)
    except Exception as e:
        return jsonify({"error": f"Failed to read players: {str(e)}"}), 500


@app.route("/api/seasons", methods=["GET"])
def get_seasons():
    try:
        seasons_csv = BASE_DIR / "dataset" / "raw" / "seasons.csv"
        if not seasons_csv.exists():
            return jsonify({"error": "seasons.csv file is missing"}), 404
            
        # Read from raw season file
        df = pd.read_csv(seasons_csv)
        records = df.to_dict(orient="records")
        cleaned_records = clean_nan_to_none(records)
        return jsonify(cleaned_records)
    except Exception as e:
        return jsonify({"error": f"Failed to read seasons: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        user_email = request.args.get("user_email")
        # Get history logged in Supabase filtered by user_email
        history = get_predictions_history(user_email=user_email, limit=50)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve history: {str(e)}"}), 500


@app.route("/api/dashboard_stats", methods=["GET"])
def get_dashboard_stats():
    try:
        players_csv = BASE_DIR / "dataset" / "raw" / "players.csv"
        seasons_csv = BASE_DIR / "dataset" / "raw" / "seasons.csv"
        
        total_players = len(pd.read_csv(players_csv)) if players_csv.exists() else 0
        total_seasons = len(pd.read_csv(seasons_csv)) if seasons_csv.exists() else 0
        
        # Extract season metrics for dashboard visualizations
        seasons_df = pd.read_csv(seasons_csv) if seasons_csv.exists() else pd.DataFrame()
        
        season_trends = []
        champions_breakdown = []
        if not seasons_df.empty:
            champs = seasons_df["champion"].value_counts().reset_index()
            champs.columns = ["champion", "titles"]
            champions_breakdown = champs.to_dict(orient="records")
            
            for _, row in seasons_df.iterrows():
                season_trends.append({
                    "season": int(row["season"]),
                    "total_runs": int(row.get("total_runs_scored", 0)) if pd.notna(row.get("total_runs_scored")) else 0,
                    "sixes": int(row.get("total_sixes", 0)) if pd.notna(row.get("total_sixes")) else 0,
                    "fours": int(row.get("total_fours", 0)) if pd.notna(row.get("total_fours")) else 0
                })
                
        return jsonify({
            "total_players": total_players,
            "total_seasons": total_seasons,
            "champions_breakdown": champions_breakdown,
            "season_trends": season_trends
        })
    except Exception as e:
        return jsonify({"error": f"Dashboard stats failure: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
