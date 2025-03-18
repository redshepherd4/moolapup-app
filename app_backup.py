from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import datetime as dt  # ✅ Forces Python to use built-in datetime
import random

app = Flask(__name__)

# ✅ Function to get pet stats as JSON
@app.route("/get_stats")
def get_stats():
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("SELECT hunger, energy, happiness, health FROM pet WHERE id=1")
    pet_stats = c.fetchone()
    conn.close()

    if pet_stats:
        return jsonify({
            "hunger": pet_stats[0],
            "energy": pet_stats[1],
            "happiness": pet_stats[2],
            "health": pet_stats[3]
        })
    else:
        return jsonify({"error": "No pet found"}), 404  # Error handling if no pet exists

# ✅ Setup Page Route
@app.route("/setup")
def setup():
    return render_template("setup.html")

# ✅ Home Page Route (Loads Pet and Seasonal Background)
@app.route("/")
def home():
    update_pet_stats()

    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("SELECT * FROM pet WHERE id = 1")
    pet = c.fetchone()
    conn.close()

    if not pet or pet[2] not in ["brown", "white", "black", "spotted"]:
        return redirect("/setup")   
    
    # ✅ Determine the correct pet image based on stats
    color = pet[2]  # "brown", "white", "black", "spotted"
    hunger, energy, happiness, health = pet[4], pet[5], pet[6], pet[7]

    pet_image = f"moolapup-{color}.png"  # Default
        
    if hunger <= 2:
        pet_image = f"moolapup-{color}-hungry.png"
    elif energy <= 2:
        pet_image = f"moolapup-{color}-tired.png"
    elif happiness <= 2:
        pet_image = f"moolapup-{color}-sad.png"
    elif health <= 2:
        pet_image = f"moolapup-{color}-sick.png"

    # ✅ Determine the season
    month = dt.datetime.now().month
    if month in [3, 4, 5]:  # March-May 
        season = "spring"
    elif month in [6, 7, 8]:  # June-August
        season = "summer"
    elif month in [9, 10, 11]:  # September-November
        season = "fall"
    else:  # December-February
        season = "winter"
    
    # ✅ Determine time of day
    current_hour = dt.datetime.now().hour
    if 6 <= current_hour < 11:
        time_of_day = "morning"
    elif 11 <= current_hour < 18:
        time_of_day = "day"
    else:
        time_of_day = "night"
    
    # ✅ Set the correct background image
    background = f"{season}-{time_of_day}.png"
    
    # ✅ Randomly select a weather effect
    weather_effect = random.choice(["clear", "rain", "snow", "leaves", "wind"])

 # ✅ Debugging print statement
    print("Pet image path:", pet_image)  # This will print in the terminal to check the image path    
   
 # ✅ FIX: Ensure `return` is properly aligned
    return render_template(
        "index.html",
        pet=pet,
        pet_image=pet_image,
        background=background,
        weather_effect=weather_effect
    )

# ✅ Database setup
def init_db():
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pet (
                    id INTEGER PRIMARY KEY,
                    name TEXT DEFAULT 'Moolapup',
                    color TEXT DEFAULT 'brown',
                    accessory TEXT DEFAULT 'none',
                    hunger INTEGER DEFAULT 5,
                    energy INTEGER DEFAULT 5,
                    happiness INTEGER DEFAULT 5,
                    health INTEGER DEFAULT 5,
                    last_updated TEXT
                )''')
    conn.commit()
    conn.close()

# ✅ Function to update pet stats every 2 hours
def update_pet_stats():
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("SELECT * FROM pet WHERE id=1")
    pet = c.fetchone()

    if pet:
        last_updated = dt.datetime.strptime(pet[8], "%Y-%m-%d %H:%M:%S")
        now = dt.datetime.now()
        time_diff_hours = (now - last_updated).total_seconds() / 3600  # Convert to hours

        if time_diff_hours >= 2:  # Updates every 2 hours
            new_hunger = min(10, pet[4] + int(time_diff_hours // 2))  # Hunger increases
            new_energy = max(0, pet[5] - int(time_diff_hours // 2))  # Energy decreases
            new_happiness = max(0, pet[6] - int(time_diff_hours // 2))  # Happiness decreases
            new_health = max(0, pet[7] - int(time_diff_hours // 3))  # Health drops slower

            # ✅ Update pet stats in the database
            c.execute("UPDATE pet SET hunger=?, energy=?, happiness=?, health=?, last_updated=? WHERE id=1",
                      (new_hunger, new_energy, new_happiness, new_health, now.strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
    conn.close()

# ✅ Interaction Route (Pet Actions)
@app.route("/interact", methods=["POST"])
def interact():
    action = request.form["action"]
    print(f"DEBUG: Action received - {action}")  # ✅ Debugging print

    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("SELECT * FROM pet WHERE id=1")
    pet = c.fetchone()

    if pet:
        hunger, energy, happiness, health = pet[4], pet[5], pet[6], pet[7]

        if action == "feed":
            new_hunger = max(0, hunger - 3)
            c.execute("UPDATE pet SET hunger=?, last_updated=? WHERE id=1",
                      (new_hunger, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        elif action == "play":
            new_happiness = min(10, happiness + 3)
            c.execute("UPDATE pet SET happiness=?, last_updated=? WHERE id=1",
                      (new_happiness, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        elif action == "rest":
            new_energy = min(10, energy + 3)
            c.execute("UPDATE pet SET energy=?, last_updated=? WHERE id=1",
                      (new_energy, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        elif action == "medical":
            new_health = min(10, health + 3)
            c.execute("UPDATE pet SET health=?, last_updated=? WHERE id=1",
                      (new_health, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
    else:
        print("DEBUG: No pet found in database")

    conn.close()
    return redirect(url_for("home"))

# ✅ Save Moolapup Selection
@app.route("/save_moolapup", methods=["POST"])
def save_moolapup():
    name = request.form.get("name")
    color = request.form.get("color")

    print(f"DEBUG: Received selection - Name: {name}, Color: {color}")

    valid_colors = ["brown", "white", "black", "spotted"]
    if color not in valid_colors:
        return "Invalid color selection", 400

    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("UPDATE pet SET name = ?, color = ? WHERE id = 1", (name, color))
    conn.commit()
    conn.close()

    return redirect("/")

# ✅ Start Flask App
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

