import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db.db_utils import get_or_create_day, execute_query

# JSON data provided by the user
DATA = """
{
  "user_profile": {
    "height_cm": 179,
    "start_weight_reference": 77.9,
    "goal": {
      "fat_loss_kg": 8,
      "muscle_gain_kg": 10
    }
  },

  "days": [
    {
      "date": "2026-03-13",
      "day_number": 1,
      "overall_rpe": 5.5,
      "gym_minutes": 30,
      "body_metrics": {
        "post_workout_weight": 77.6
      },
      "activity": null,
      "sleep": null,
      "soreness": [],
      "workout": {
        "duration_minutes": 30,
        "exercises": [
          {
            "name": "Treadmill",
            "muscle_group": "cardio",
            "sets": [
              {"set": 1, "speed": 6, "duration_min": 1.5},
              {"set": 2, "speed": 10, "duration_min": 2.75},
              {"set": 3, "speed": 6, "duration_min": 0.75}
            ]
          },
          {
            "name": "Bicep Curl (Machine)",
            "muscle_group": "biceps",
            "sets": [
              {"set": 1, "weight_lbs": 10, "reps": 10},
              {"set": 2, "weight_lbs": 20, "reps": 10},
              {"set": 3, "weight_lbs": 30, "reps": 5}
            ]
          },
          {
            "name": "Pec Fly (Machine)",
            "muscle_group": "chest",
            "sets": [
              {"set": 1, "weight_lbs": 50, "reps": 10},
              {"set": 2, "weight_lbs": 60, "reps": 10},
              {"set": 3, "weight_lbs": 70, "reps": 10}
            ]
          },
          {
            "name": "Bicep Curl (Dumbbell)",
            "muscle_group": "biceps",
            "sets": [
              {"set": 1, "weight_kg": 10, "reps": 10}
            ]
          },
          {
            "name": "Abdominal Crunch",
            "muscle_group": "abs",
            "sets": [
              {"set": 1, "weight_lbs": 70, "reps": 10},
              {"set": 2, "weight_lbs": 80, "reps": 10},
              {"set": 3, "weight_lbs": 90, "reps": 10}
            ]
          },
          {
            "name": "Tricep Extension (Machine)",
            "muscle_group": "triceps",
            "sets": [
              {"set": 1, "weight_lbs": 30, "reps": 10},
              {"set": 2, "weight_lbs": 40, "reps": 10},
              {"set": 3, "weight_lbs": 50, "reps": 10}
            ]
          }
        ]
      },
      "meals": []
    },

    {
      "date": "2026-03-14",
      "day_number": 2,
      "overall_rpe": null,
      "gym_minutes": 0,
      "body_metrics": null,
      "activity": {
        "move_calories": 750,
        "exercise_minutes": 79,
        "stand_hours": 9,
        "steps": 15087,
        "distance_km": 10.03
      },
      "sleep": {
        "total_sleep_minutes": 468
      },
      "soreness": [
        {"body_part": "elbow_area", "score": 8}
      ],
      "workout": null,
      "meals": [
        {
          "meal_type": "lunch",
          "description": "chicken malai mirch kathi roll + half oreo cheese pancake"
        },
        {
          "meal_type": "dinner",
          "description": "tuna + eggs (half eaten)"
        },
        {
          "meal_type": "supper",
          "description": "airfried chicken drumsticks with seasoning + cucumber + radish"
        }
      ]
    },

    {
      "date": "2026-03-15",
      "day_number": 3,
      "overall_rpe": null,
      "gym_minutes": 0,
      "body_metrics": {
        "post_workout_weight": 78.4
      },
      "activity": {
        "move_calories": 643,
        "exercise_minutes": 57,
        "stand_hours": 13,
        "steps": 12153,
        "distance_km": 7.63
      },
      "sleep": {
        "total_sleep_minutes": 317
      },
      "soreness": [
        {"body_part": "left_arm", "score": 1},
        {"body_part": "right_arm", "score": 8.5}
      ],
      "workout": null,
      "meals": [
        {
          "meal_type": "lunch",
          "description": "chicken karahi + rice + radish + green chilli"
        },
        {
          "meal_type": "dinner",
          "description": "3 chicken drumsticks with tandoori seasoning"
        }
      ]
    },

    {
      "date": "2026-03-16",
      "day_number": 4,
      "overall_rpe": 3.5,
      "gym_minutes": 45,
      "body_metrics": {
        "pre_workout_weight": 79.0,
        "post_workout_weight": 78.3
      },
      "activity": {
        "move_calories": 764,
        "exercise_minutes": 89,
        "stand_hours": 12,
        "steps": 17104,
        "distance_km": 11.17
      },
      "sleep": {
        "total_sleep_minutes": 400
      },
      "soreness": [
        {"body_part": "left_arm", "score": 0.5},
        {"body_part": "right_arm", "score": 4.5},
        {"body_part": "abs", "score": 3},
        {"body_part": "legs", "score": 3.5}
      ],
      "workout": {
        "duration_minutes": 45,
        "exercises": [
          {
            "name": "Tricep Extension (Machine)",
            "muscle_group": "triceps",
            "sets": [
              {"set": 1, "weight_lbs": 30, "reps": 10},
              {"set": 2, "weight_lbs": 40, "reps": 10},
              {"set": 3, "weight_lbs": 50, "reps": 10},
              {"set": 4, "weight_lbs": 60, "reps": 10}
            ]
          },
          {
            "name": "Abdominal Crunch",
            "muscle_group": "abs",
            "sets": [
              {"set": 1, "weight_lbs": 70, "reps": 10},
              {"set": 2, "weight_lbs": 80, "reps": 10},
              {"set": 3, "weight_lbs": 90, "reps": 10},
              {"set": 4, "weight_lbs": 100, "reps": 5}
            ]
          },
          {
            "name": "Leg Press",
            "muscle_group": "legs",
            "sets": [
              {"set": 1, "weight_lbs": 120, "reps": 10},
              {"set": 2, "weight_lbs": 160, "reps": 10},
              {"set": 3, "weight_lbs": 200, "reps": 10},
              {"set": 4, "weight_lbs": 240, "reps": 10}
            ]
          },
          {
            "name": "Rear Delt Machine",
            "muscle_group": "shoulders",
            "sets": [
              {"set": 1, "weight_lbs": 30, "reps": 10},
              {"set": 2, "weight_lbs": 50, "reps": 10},
              {"set": 3, "weight_lbs": 70, "reps": 5}
            ]
          },
          {
            "name": "Pec Fly (Machine)",
            "muscle_group": "chest",
            "sets": [
              {"set": 1, "weight_lbs": 30, "reps": 10},
              {"set": 2, "weight_lbs": 50, "reps": 10},
              {"set": 3, "weight_lbs": 70, "reps": 10}
            ]
          }
        ]
      },
      "meals": [
        {
          "meal_type": "lunch",
          "description": "2 plates hainanese chicken rice"
        },
        {
          "meal_type": "dinner",
          "description": "rice + pasta sauce + mixed veggies + 2 drumsticks + 4 eggs + brussels sprouts + yogurt"
        }
      ]
    }
  ]
}
"""

def run():
    print("Parsing JSON data...")
    data = json.loads(DATA)
    
    for day_data in data.get('days', []):
        date_str = day_data['date']
        rpe = day_data.get('overall_rpe')
        gym_mins = day_data.get('gym_minutes')
        
        day_id = get_or_create_day(date_str)
        execute_query("UPDATE days SET overall_rpe = ?, gym_minutes = ? WHERE id = ?", (rpe, gym_mins, day_id))
        
        bm = day_data.get('body_metrics')
        if bm:
            pre_w = bm.get('pre_workout_weight')
            post_w = bm.get('post_workout_weight')
            morn_w = bm.get('morning_weight', pre_w if pre_w else post_w)
            execute_query(
                "INSERT INTO body_metrics (day_id, morning_weight, pre_workout_weight, post_workout_weight) VALUES (?, ?, ?, ?) ON CONFLICT(day_id) DO UPDATE SET morning_weight=excluded.morning_weight, pre_workout_weight=excluded.pre_workout_weight, post_workout_weight=excluded.post_workout_weight",
                (day_id, morn_w, pre_w, post_w)
            )
            
        act = day_data.get('activity')
        if act:
            execute_query(
                "INSERT INTO activity_logs (day_id, move_calories, exercise_minutes, stand_hours, steps, distance_km) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(day_id) DO UPDATE SET move_calories=excluded.move_calories, exercise_minutes=excluded.exercise_minutes, stand_hours=excluded.stand_hours, steps=excluded.steps, distance_km=excluded.distance_km",
                (day_id, act.get('move_calories'), act.get('exercise_minutes'), act.get('stand_hours'), act.get('steps'), act.get('distance_km'))
            )
            
        slp = day_data.get('sleep')
        if slp:
            execute_query("INSERT INTO sleep_logs (day_id, total_sleep_minutes) VALUES (?, ?) ON CONFLICT(day_id) DO UPDATE SET total_sleep_minutes=excluded.total_sleep_minutes", (day_id, slp.get('total_sleep_minutes')))
            
        for sor in day_data.get('soreness', []):
            execute_query("INSERT INTO soreness_logs (day_id, body_part, soreness_score) VALUES (?, ?, ?)",
                          (day_id, sor.get('body_part'), sor.get('score')))
            
        for meal in day_data.get('meals', []):
            execute_query("INSERT INTO meals (day_id, meal_type, description) VALUES (?, ?, ?)",
                          (day_id, meal.get('meal_type'), meal.get('description')))
            
        wo = day_data.get('workout')
        if wo:
            cursor = execute_query("INSERT INTO workouts (day_id, duration_minutes) VALUES (?, ?)", (day_id, wo.get('duration_minutes')))
            wo_id = cursor.lastrowid
            
            for ex in wo.get('exercises', []):
                ex_cursor = execute_query("INSERT INTO exercise_entries (workout_id, exercise_name, muscle_group) VALUES (?, ?, ?)",
                                          (wo_id, ex.get('name'), ex.get('muscle_group')))
                ex_id = ex_cursor.lastrowid
                
                for s in ex.get('sets', []):
                    weight = s.get('weight_lbs') or s.get('weight_kg') or s.get('speed')
                    
                    unit = 'kg'
                    if 'weight_lbs' in s:
                        unit = 'lbs'
                    elif 'speed' in s:
                        unit = 'speed'
                        
                    reps = s.get('reps') or s.get('duration_min')
                    execute_query(
                        "INSERT INTO exercise_sets (exercise_entry_id, set_number, weight, reps, unit) VALUES (?, ?, ?, ?, ?)",
                        (ex_id, s.get('set'), weight, reps, unit)
                    )
                    
    print("Database seeded completely!")

if __name__ == "__main__":
    run()
