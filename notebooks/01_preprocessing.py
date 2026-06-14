import pandas as pd
import numpy as np
import os
def preprocess_data():
    print("Starting data preprocessing...")
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "dataset", "raw")
    processed_dir = os.path.join(base_dir, "dataset", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    deliveries_path = os.path.join(raw_dir, "deliveries.csv")
    matches_path = os.path.join(raw_dir, "matches.csv")
    
    # Load CSVs
    print("Loading raw CSV files...")
    deliveries = pd.read_csv(deliveries_path)
    matches = pd.read_csv(matches_path)
    
    # Remove duplicates
    deliveries = deliveries.drop_duplicates()
    matches = matches.drop_duplicates()
    
    # Convert is_wicket to boolean integer
    deliveries["is_wicket"] = (
        deliveries["is_wicket"]
        .astype(str)
        .str.upper()
        .map({"TRUE": 1, "FALSE": 0})
        .fillna(0)
        .astype(int)
    )
    
    # Filter only normal matches with valid winners
    matches_clean = matches[
        (matches["result"] == "normal") & 
        (matches["winner"].notna())
    ].copy()
    
    # Target score is first innings score + 1
    matches_clean["target_score"] = matches_clean["first_innings_score"] + 1
    
    # Focus only on second innings (chasing team)
    second_innings = deliveries[deliveries["innings"] == 2].copy()
    
    # Merge matches metadata into second innings
    data = second_innings.merge(
        matches_clean[["match_id", "winner", "target_score"]],
        on="match_id",
        how="inner"
    )
    
    # Sort data chronologically per ball
    data = data.sort_values(["match_id", "over", "ball", "delivery_id"])
    
    # Handle legal balls vs extra runs (wide/no-ball don't count as legal balls in the over)
    data["extra_type"] = data["extra_type"].fillna("").astype(str).str.lower().str.strip()
    data["legal_ball"] = (~data["extra_type"].isin([
        "wide", "wides", "no ball", "noball", "no-ball"
    ])).astype(int)
    
    # Cumulative calculations per match
    data["current_score"] = data.groupby("match_id")["total_runs"].cumsum()
    data["wickets_lost"] = data.groupby("match_id")["is_wicket"].cumsum()
    data["balls_bowled"] = data.groupby("match_id")["legal_ball"].cumsum()
    
    # T20 legal balls left
    data["balls_left"] = 120 - data["balls_bowled"]
    data["runs_left"] = data["target_score"] - data["current_score"]
    data["wickets_left"] = 10 - data["wickets_lost"]
    data["chasing_team"] = data["batting_team"]
    
    # Chasing team outcome (1 if they won, 0 if lost)
    data["chasing_team_won"] = (data["chasing_team"] == data["winner"]).astype(int)
    
    # Current Run Rate (CRR)
    data["current_run_rate"] = np.where(
        data["balls_bowled"] > 0,
        data["current_score"] / (data["balls_bowled"] / 6.0),
        0.0
    )
    
    # Required Run Rate (RRR)
    data["required_run_rate"] = np.where(
        data["balls_left"] > 0,
        data["runs_left"] / (data["balls_left"] / 6.0),
        0.0
    )
    
    # Filter invalid rows (ensure boundaries)
    final_data = data[
        (data["balls_left"] >= 0) &
        (data["balls_left"] <= 120) &
        (data["wickets_left"] >= 0) &
        (data["wickets_left"] <= 10) &
        (data["runs_left"] >= 0)
    ].copy()
    
    # Feature selection
    features = [
        "target_score",
        "current_score",
        "runs_left",
        "balls_left",
        "wickets_left",
        "current_run_rate",
        "required_run_rate"
    ]
    target = "chasing_team_won"
    metadata = ["match_id", "chasing_team", "bowling_team"]
    
    ml_dataset = final_data[features + [target] + metadata]
    
    output_path = os.path.join(processed_dir, "win_probability_dataset.csv")
    ml_dataset.to_csv(output_path, index=False)
    
    print(f"Data preprocessing complete. Preprocessed shape: {ml_dataset.shape}")
    print(f"Saved dataset to {output_path}")
if __name__ == "__main__":
    preprocess_data()
