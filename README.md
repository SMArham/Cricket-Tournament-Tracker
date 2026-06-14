# Cricket Tournament Tracker

This project is a complete end-to-end Machine Learning tournament tracker and live predictor built for the **Machine Learning** course. It calculates win probabilities for chasing teams in the second innings of a cricket match using real-time game situation features.

The application uses a trained **Random Forest Classifier** model and connects to a **Supabase Cloud Database** to store user credentials and isolated simulation logs.

---

## 1. Project Title
**Cricket Tournament Tracker**

---

## 2. Problem Statement
In a cricket match, predicting the win probability of a chasing team in the 2nd innings is a complex, non-linear problem. The outcome is highly sensitive to the runs remaining, balls left, wickets in hand, and the respective run rates. This project implements a classification model to evaluate the chasing team's situational winning chances at any given ball.

---

## 3. Dataset Description
The model is trained entirely on historical IPL statistics. No fake rows or hardcoded datasets are used. The application reads directly from the raw CSV data located inside `dataset/raw/`.

---

## 4. Dataset File Names and Columns

### 1) `dataset/raw/deliveries.csv`
*   **Columns**: `delivery_id`, `match_id`, `innings`, `over`, `ball`, `batting_team`, `bowling_team`, `striker`, `non_striker`, `bowler`, `batsman_runs`, `extra_runs`, `total_runs`, `extra_type`, `is_wicket`, `dismissal_type`, `dismissed_player`, `fielder`

### 2) `dataset/raw/matches.csv`
*   **Columns**: `match_id`, `season`, `match_number`, `stage`, `date`, `venue`, `city`, `team1`, `team2`, `toss_winner`, `toss_decision`, `first_innings_score`, `first_innings_wickets`, `first_innings_overs`, `second_innings_score`, `second_innings_wickets`, `second_innings_overs`, `result`, `winner`, `win_by`, `win_margin`, `player_of_match`, `umpire1`, `umpire2`, `is_day_night`

### 3) `dataset/raw/players.csv`
*   **Columns**: `player_id`, `player_name`, `nationality`, `dob_year`, `batting_style`, `bowling_style`, `playing_role`, `ipl_debut_season`, `last_season_played`, `is_capped_international`, `base_price_lakh`, `highest_auction_price_lakh`

### 4) `dataset/raw/seasons.csv`
*   **Columns**: `season`, `total_matches`, `num_teams`, `champion`, `runner_up`, `orange_cap_winner`, `purple_cap_winner`, `most_valuable_player`, `total_runs_scored`, `total_sixes`, `total_fours`, `avg_first_innings_score`, `highest_team_total`, `lowest_team_total`

---

## 5. ML Task Type
**Binary Classification**  
The model predicts the likelihood of the chasing team winning.

---

## 6. Features Used
1.  `target_score` (1st Innings total + 1)
2.  `current_score` (Cumulative runs scored in the 2nd innings)
3.  `runs_left` (Runs remaining to chase down the target)
4.  `balls_left` (Legal deliveries remaining, out of 120)
5.  `wickets_left` (Wickets remaining, 10 - wickets lost)
6.  `current_run_rate` (CRR)
7.  `required_run_rate` (RRR)

---

## 7. Target Column
*   **Target Column**: `chasing_team_won`
*   **Target Values**:
    *   `1` = chasing team won (`batting_team == winner`)
    *   `0` = chasing team lost (`batting_team != winner`)

---

## 8. Algorithms Used
*   Logistic Regression
*   k-Nearest Neighbors (KNN)
*   Decision Tree Classifier
*   **Random Forest Classifier** (Selected as the best-performing model)

---

## 9. Evaluation Metrics
Models are benchmarked using:
*   Accuracy (Random Forest: 55.00%)
*   Precision (Random Forest: 60.12%)
*   Recall
*   F1-score
*   Confusion Matrix
*   Classification Report

---

## 10. Folder Structure
```text
ML_Cricket_Tracker/
│
├── dataset/
│   ├── raw/
│   │   ├── deliveries.csv
│   │   ├── matches.csv
│   │   ├── players.csv
│   │   └── seasons.csv
│   │
│   └── processed/
│       └── win_probability_dataset.csv
│
├── notebooks/
│   ├── 01_preprocessing.ipynb
│   ├── 01_preprocessing.py
│   ├── 02_model_training.ipynb
│   └── 02_model_training.py
│
├── model/
│   ├── model.pkl
│   ├── scaler.pkl
│   ├── feature_columns.json
│   └── model_metrics.json
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── prediction_service.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── predictor.html
│   ├── dashboard.html
│   ├── players.html
│   ├── seasons.html
│   ├── style.css
│   └── script.js
│
├── report/
│   └── project_report.md
│
└── README.md
```

---

## 11. Setup Instructions

1.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    ```
2.  **Activate Virtual Environment**:
    *   *Windows (cmd)*: `venv\Scripts\activate`
    *   *Windows (PowerShell)*: `.\venv\Scripts\activate.ps1`
    *   *macOS/Linux*: `source venv/bin/activate`
3.  **Install Packages**:
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Setup Supabase Database Columns**:
    Run this SQL command in your Supabase dashboard SQL Editor to enable user-specific logging:
    ```sql
    ALTER TABLE public.predictions ADD COLUMN user_email TEXT;
    ```

---

## 12. Run Instructions

1.  **Generate Processed Dataset**:
    ```bash
    python notebooks/01_preprocessing.py
    ```
2.  **Train Models and Export Binaries**:
    ```bash
    python notebooks/02_model_training.py
    ```
3.  **Start Flask Web Server**:
    ```bash
    python backend/app.py
    ```
4.  **Open URL in Web Browser**:
    *   Navigate to: **`http://127.0.0.1:5000`**

---

## 13. API Endpoints

*   `POST /api/predict`: Validates input values, computes real-time game features, queries the Random Forest classifier, and logs outcomes to Supabase.
*   `GET /api/players`: Reads directly from `dataset/raw/players.csv` and returns players roster as JSON.
*   `GET /api/seasons`: Reads directly from `dataset/raw/seasons.csv` and returns seasons records as JSON.
*   `GET /api/history`: Retrieves logged predictions list from Supabase, filtered by the logged-in user.
*   `GET /api/dashboard_stats`: Helper endpoint for summary totals and visual Chart.js trends.

---

## 14. Screenshots Placeholder
Place visual interfaces snapshots under the `/report` folder and reference them here:
*   *Landing & Signup Mockup*: `![Home Mockup](report/screenshot_home.png)`
*   *Predictor Page Mockup*: `![Predictor Mockup](report/screenshot_predictor.png)`
*   *Dashboard Analytics Mockup*: `![Dashboard Mockup](report/screenshot_dashboard.png)`

---

## 15. Deployment Instructions
For production deployment, see the step-by-step instructions in the [deployment_guide.md](file:///c:/Users/muham/Downloads/ML_Cricket_Tracker/deployment_guide.md) file in the root folder of this project.

Briefly:
1.  **Backend**: Deploy the root folder on Render using Build Command `pip install -r backend/requirements.txt` and Start Command `gunicorn backend.app:app`. Set environment variables in the Render dashboard.
2.  **Frontend**: Deploy on Vercel setting the **Root Directory** as `frontend`. Ensure you update the `API_BASE` variable in `frontend/script.js` to your deployed Render URL first.

---

## 16. GitHub Submission Checklist
- [x] All raw datasets are under `dataset/raw/`
- [x] No hardcoded or fake dataset rows are loaded
- [x] Both Jupyter notebooks (`.ipynb`) are present and executed
- [x] `/model` folder contains `model.pkl`, `scaler.pkl`, and `feature_columns.json`
- [x] Connected to Supabase cloud database for secure logins and predictions logging
- [x] HTML, CSS, and JS files are placed in `frontend/`
- [x] `backend/requirements.txt` lists all required dependencies
- [x] CCP-style markdown report exists at `report/project_report.md`
- [x] System executes and runs on `http://127.0.0.1:5000`
