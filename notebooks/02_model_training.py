import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
def train_model():
    print("Starting model training...")
    
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "dataset", "processed", "win_probability_dataset.csv")
    model_dir = os.path.join(base_dir, "model")
    os.makedirs(model_dir, exist_ok=True)
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}. Please run preprocessing first.")
        
    # Load dataset
    df = pd.read_csv(dataset_path)
    print(f"Loaded processed dataset with shape: {df.shape}")
    
    # Define features and target
    feature_columns = [
        "target_score",
        "current_score",
        "runs_left",
        "balls_left",
        "wickets_left",
        "current_run_rate",
        "required_run_rate"
    ]
    
    X = df[feature_columns]
    y = df["chasing_team_won"]
    groups = df["match_id"]
    
    # GroupShuffleSplit to avoid splitting balls from the same match across train and test sets
    print("Splitting data by matches...")
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]
    
    print(f"Train size: {X_train.shape[0]} balls, Test size: {X_test.shape[0]} balls")
    
    # Scaling
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Models to compare
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=7),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42) # depth limit to avoid overfitting and keep size smaller
    }
    
    results = []
    print("Training and evaluating models...")
    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        print(f"{name} -> Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")
        results.append({
            "Model": name,
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "F1 Score": f1
        })
        
    results_df = pd.DataFrame(results)
    
    # Select Random Forest as the primary model
    best_model_name = "Random Forest"
    print(f"\nSelecting {best_model_name} as the best model for export...")
    best_model = models[best_model_name]
    
    # Print final evaluation report
    y_pred_best = best_model.predict(X_test_scaled)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred_best))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred_best))
    
    # Export model binaries
    model_path = os.path.join(model_dir, "model.pkl")
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    features_path = os.path.join(model_dir, "feature_columns.json")
    
    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)
        
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
        
    with open(features_path, "w") as f:
        json.dump(feature_columns, f)
        
    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")
    print(f"Feature config saved to {features_path}")
    
    # Save a JSON file with model metrics to use in backend/reports
    metrics_path = os.path.join(model_dir, "model_metrics.json")
    metrics = {
        "best_model": best_model_name,
        "features": feature_columns,
        "comparison": results,
        "classification_report": classification_report(y_test, y_pred_best, output_dict=True)
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
        
    print(f"Metrics saved to {metrics_path}")
if __name__ == "__main__":
    train_model()
