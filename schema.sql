CREATE TABLE IF NOT EXISTS days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL, -- YYYY-MM-DD
    notes TEXT,
    overall_rpe INTEGER,
    gym_minutes INTEGER
);

CREATE TABLE IF NOT EXISTS body_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id),
    morning_weight REAL,
    pre_workout_weight REAL,
    post_workout_weight REAL
);

CREATE TABLE IF NOT EXISTS sleep_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id),
    total_sleep_minutes INTEGER,
    hr_min INTEGER,
    hr_max INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id),
    move_calories REAL,
    exercise_minutes INTEGER,
    stand_hours INTEGER,
    steps INTEGER,
    distance_km REAL
);

CREATE TABLE IF NOT EXISTS soreness_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id),
    body_part TEXT,
    soreness_score INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id),
    duration_minutes INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS exercise_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER REFERENCES workouts(id),
    exercise_name TEXT NOT NULL,
    muscle_group TEXT,
    equipment TEXT,
    pain_flag BOOLEAN
);

CREATE TABLE IF NOT EXISTS exercise_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_entry_id INTEGER REFERENCES exercise_entries(id),
    set_number INTEGER,
    weight REAL,
    reps INTEGER,
    unit TEXT DEFAULT 'kg'
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id),
    meal_type TEXT,
    description TEXT,
    calories REAL,
    protein REAL,
    carbs REAL,
    fat REAL,
    fiber REAL,
    is_estimated BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_id INTEGER REFERENCES meals(id),
    food_name TEXT,
    quantity REAL,
    unit TEXT,
    calories REAL,
    protein REAL,
    carbs REAL,
    fat REAL,
    fiber REAL
);

CREATE TABLE IF NOT EXISTS daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id),
    total_calories REAL,
    total_protein REAL,
    total_carbs REAL,
    total_fat REAL,
    total_fiber REAL
);
