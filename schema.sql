CREATE TABLE IF NOT EXISTS days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL, -- YYYY-MM-DD
    notes TEXT,
    overall_rpe REAL,
    gym_minutes INTEGER
);

CREATE TABLE IF NOT EXISTS body_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
    weight REAL
);

CREATE TABLE IF NOT EXISTS sleep_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
    total_sleep_minutes INTEGER,
    hr_min INTEGER,
    hr_max INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
    move_calories REAL,
    exercise_minutes INTEGER,
    stand_hours INTEGER,
    steps INTEGER,
    distance_km REAL
);

CREATE TABLE IF NOT EXISTS soreness_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id) ON DELETE CASCADE,
    body_part TEXT,
    soreness_score INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id) ON DELETE CASCADE,
    duration_minutes INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS exercise_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    muscle_group TEXT,
    equipment TEXT,
    pain_flag BOOLEAN
);

CREATE TABLE IF NOT EXISTS exercise_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_entry_id INTEGER REFERENCES exercise_entries(id) ON DELETE CASCADE,
    set_number INTEGER,
    weight REAL,
    reps INTEGER,
    unit TEXT DEFAULT 'kg'
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id) ON DELETE CASCADE,
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
    meal_id INTEGER REFERENCES meals(id) ON DELETE CASCADE,
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
    day_id INTEGER UNIQUE REFERENCES days(id) ON DELETE CASCADE,
    total_calories REAL,
    total_protein REAL,
    total_carbs REAL,
    total_fat REAL,
    total_fiber REAL
);

CREATE TABLE IF NOT EXISTS cardio_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id INTEGER REFERENCES days(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    interval_number INTEGER,
    duration_min REAL,
    speed_kmh REAL,
    distance_km REAL,
    incline_pct REAL,
    avg_hr INTEGER
);

CREATE TABLE IF NOT EXISTS exercise_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT UNIQUE NOT NULL,
    canonical_name TEXT NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_days_date ON days(date);
CREATE INDEX IF NOT EXISTS idx_body_metrics_day_id ON body_metrics(day_id);
CREATE INDEX IF NOT EXISTS idx_sleep_logs_day_id ON sleep_logs(day_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_day_id ON activity_logs(day_id);
CREATE INDEX IF NOT EXISTS idx_workouts_day_id ON workouts(day_id);
CREATE INDEX IF NOT EXISTS idx_exercise_entries_workout_id ON exercise_entries(workout_id);
CREATE INDEX IF NOT EXISTS idx_exercise_entries_name ON exercise_entries(exercise_name);
CREATE INDEX IF NOT EXISTS idx_exercise_sets_entry_id ON exercise_sets(exercise_entry_id);
CREATE INDEX IF NOT EXISTS idx_meals_day_id ON meals(day_id);
CREATE INDEX IF NOT EXISTS idx_foods_meal_id ON foods(meal_id);
CREATE INDEX IF NOT EXISTS idx_daily_summary_day_id ON daily_summary(day_id);
CREATE INDEX IF NOT EXISTS idx_cardio_logs_day_id ON cardio_logs(day_id);
