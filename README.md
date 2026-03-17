# Gym Tracker

A local-first, personal fitness tracking system built with Python, SQLite, and Streamlit.
Track your daily metrics (weight, sleep, activity), log workouts and exercises, and visualize progress locally.

## Project Structure

- `gym_log.db`: Auto-generated SQLite database.
- `schema.sql`: SQL schema defining all tables.
- `db/`: Database configuration and initialization code.
- `scripts/`: Python CLI scripts for adding tracking data from the terminal.
- `app/`: Streamlit dashboard codebase.
- `data/backups/`: Directory for database backups.

## Setup Instructions

1. **Install Dependencies**
   Ensure you have Python installed, then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the Database**
   Before running anything, create the SQLite database using:
   ```bash
   python db/init_db.py
   ```
   This will read `schema.sql` and produce `gym_log.db` in this folder.

## Usage

### 1. Data Logging (CLI)
You can log data using the minimal terminal scripts in the `scripts/` directory:

- **Log Daily Metrics** (Sleep, weight, general activity, soreness):
  ```bash
  python scripts/insert_day.py
  ```

- **Log a Workout** (Exercises, sets, weights):
  ```bash
  python scripts/insert_workout.py
  ```

- **Log a Meal** (Macros and calories):
  ```bash
  python scripts/insert_meal.py
  ```

### 2. Streamlit Dashboard
To view your progress visually, start the local Streamlit server:

```bash
streamlit run app/app.py
```
This will open up a localhost web page in your default browser where you can view charts mapping weight, sleep, habits, and exercise progression.

## Backups
It is highly recommended to periodically copy `gym_log.db` into `data/backups/` so you do not lose your logging history.
