import sys
import os
from datetime import date

# Add parent directory to path to import db
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db.db_utils import get_or_create_day, execute_query

def main():
    print("--- Log a Meal ---")
    date_str = input(f"Enter date (YYYY-MM-DD) [default today {date.today()}]: ").strip()
    if not date_str:
        date_str = str(date.today())

    day_id = get_or_create_day(date_str)
    
    meal_type = input("Meal type (e.g. Breakfast, Lunch, Dinner, Snack): ")
    desc = input("Description: ")
    
    cal = input("Total Calories: ")
    pro = input("Total Protein (g): ")
    car = input("Total Carbs (g): ")
    fat = input("Total Fat (g): ")
    
    cal = float(cal) if cal else None
    pro = float(pro) if pro else None
    car = float(car) if car else None
    fat = float(fat) if fat else None
    
    cursor = execute_query(
        "INSERT INTO meals (day_id, meal_type, description, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (day_id, meal_type, desc, cal, pro, car, fat)
    )
    meal_id = cursor.lastrowid
    
    print(f"Logged {meal_type} successfully.")

if __name__ == "__main__":
    main()
