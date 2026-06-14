import pickle
import json
import pandas as pd
import numpy as np
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")
class PredictionService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.is_loaded = False
        self.load_model()
        
    def load_model(self):
        model_path = os.path.join(MODEL_DIR, "model.pkl")
        scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
        features_path = os.path.join(MODEL_DIR, "feature_columns.json")
        
        if os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(features_path):
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                with open(features_path, "r") as f:
                    self.feature_columns = json.load(f)
                self.is_loaded = True
                print("ML Model and Scaler loaded successfully.")
            except Exception as e:
                print(f"Error loading model files: {e}")
                self.is_loaded = False
        else:
            print("Model files not found. Model training is required.")
            self.is_loaded = False
    def predict(self, chasing_team, defending_team, target_score, current_score, 
                completed_overs, current_over_balls, wickets_lost):
        if not self.is_loaded:
            # Attempt to reload in case files were recently generated
            self.load_model()
            if not self.is_loaded:
                return {"error": "Model files are not initialized on the server. Please train the model."}
        # Validate basic boundaries
        if chasing_team.lower().strip() == defending_team.lower().strip():
            return {"error": "Chasing and defending teams cannot be the same."}
            
        if completed_overs < 0 or completed_overs > 19:
            return {"error": "Completed overs must be between 0 and 19."}
            
        if current_over_balls < 0 or current_over_balls > 5:
            return {"error": "Balls in current over must be between 0 and 5."}
            
        if wickets_lost < 0 or wickets_lost > 10:
            return {"error": "Wickets lost must be between 0 and 10."}
        # Calculations
        balls_bowled = completed_overs * 6 + current_over_balls
        balls_left = 120 - balls_bowled
        
        if balls_left < 0:
            return {"error": "Overs cannot exceed 20 overs (120 legal balls)."}
        runs_left = target_score - current_score
        wickets_left = 10 - wickets_lost
        
        # If chasing team already reached target
        if runs_left <= 0:
            return {
                "predicted_winner": chasing_team,
                "chasing_team": chasing_team,
                "defending_team": defending_team,
                "chasing_win_probability": 100.0,
                "defending_win_probability": 0.0,
                "runs_left": max(0, runs_left),
                "balls_left": balls_left,
                "wickets_left": wickets_left,
                "current_run_rate": round(current_score / (balls_bowled / 6.0) if balls_bowled > 0 else 0.0, 2),
                "required_run_rate": 0.0
            }
            
        # If chasing team lost all wickets and didn't reach target
        if wickets_left <= 0:
            return {
                "predicted_winner": defending_team,
                "chasing_team": chasing_team,
                "defending_team": defending_team,
                "chasing_win_probability": 0.0,
                "defending_win_probability": 100.0,
                "runs_left": runs_left,
                "balls_left": balls_left,
                "wickets_left": 0,
                "current_run_rate": round(current_score / (balls_bowled / 6.0) if balls_bowled > 0 else 0.0, 2),
                "required_run_rate": 0.0
            }
        # Run Rates
        current_run_rate = current_score / (balls_bowled / 6.0) if balls_bowled > 0 else 0.0
        required_run_rate = runs_left / (balls_left / 6.0) if balls_left > 0 else 0.0
        # Construct feature DataFrame
        input_data = pd.DataFrame([{
            "target_score": target_score,
            "current_score": current_score,
            "runs_left": runs_left,
            "balls_left": balls_left,
            "wickets_left": wickets_left,
            "current_run_rate": current_run_rate,
            "required_run_rate": required_run_rate
        }])
        # Align with training columns
        input_data = input_data[self.feature_columns]
        
        # Scale
        input_scaled = self.scaler.transform(input_data)
        
        # Predict Probabilities
        probabilities = self.model.predict_proba(input_scaled)[0]
        
        # Map classes: 0 = chasing team lost, 1 = chasing team won
        defending_win_prob = round(probabilities[0] * 100, 2)
        chasing_win_prob = round(probabilities[1] * 100, 2)
        
        predicted_winner = chasing_team if chasing_win_prob >= defending_win_prob else defending_team
        return {
            "predicted_winner": predicted_winner,
            "chasing_team": chasing_team,
            "defending_team": defending_team,
            "chasing_win_probability": chasing_win_prob,
            "defending_win_probability": defending_win_prob,
            "runs_left": runs_left,
            "balls_left": balls_left,
            "wickets_left": wickets_left,
            "current_run_rate": round(current_run_rate, 2),
            "required_run_rate": round(required_run_rate, 2)
        }
