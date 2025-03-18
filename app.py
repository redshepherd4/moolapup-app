from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import datetime as dt  # ✅ Forces Python to use built-in datetime
import random
import string
import os

# ✅ Define `init_db()` at the top so it's ready before being called
def init_db():
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()

    print("🔧 Initializing database...")  # ✅ Debugging

    # ✅ Ensure table is created
    c.execute('''CREATE TABLE IF NOT EXISTS pet (
        id INTEGER PRIMARY KEY,
        pet_id TEXT UNIQUE,
        name TEXT DEFAULT 'Moolapup',
        color TEXT DEFAULT 'brown',
        accessory TEXT DEFAULT 'none',
        hunger INTEGER DEFAULT 5,
        energy INTEGER DEFAULT 5,
        happiness INTEGER DEFAULT 5,
        health INTEGER DEFAULT 5,
        last_updated TEXT
    )''')

    print("✅ Database table 'pet' checked/created.")  # ✅ Debugging

    conn.commit()
    conn.close()

# ✅ Ensure database is created BEFORE Flask starts
init_db()

app = Flask(__name__)

# ✅ Debugging: Ensure app starts properly
print("🚀 Flask app is running!")

if __name__ == "__main__":
    init_db()  # ✅ Moves this after the function definition
    app.run(host="0.0.0.0", port=10000)  # Required for Render

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
@app.route("/<pet_id>")
def home(pet_id):
    update_pet_stats(pet_id)

    conn = sqlite3.connect("pet.db")
    c = conn.cursor()   
    c.execute("SELECT * FROM pet WHERE pet_id=?", (pet_id,))
    pet = c.fetchone()
    conn.close()

    if not pet or pet[3] not in ["brown", "white", "black", "spotted"]:
        return redirect("/setup")

    color = pet[3]
    hunger, energy, happiness, health = pet[5], pet[6], pet[7], pet[8]

    pet_image = f"moolapup-{color}.png"
    if hunger > 0 and hunger <= 2:
        pet_image = f"moolapup-{color}-hungry.png"
    elif energy <= 2:
        pet_image = f"moolapup-{color}-tired.png"
    elif happiness <= 2:
        pet_image = f"moolapup-{color}-sad.png"
    elif health <= 2:
        pet_image = f"moolapup-{color}-sick.png"
    else:
        pet_image = f"moolapup-{color}.png"

    month = dt.datetime.now().month
    if month in [3, 4, 5]:
        season = "spring"
        weather_options = ["rain", "clear", "wind"]
    elif month in [6, 7, 8]:
        season = "summer"
        weather_options = ["clear", "wind", "storm"]
    elif month in [9, 10, 11]:
        season = "fall"
        weather_options = ["leaves", "wind", "clear"]
    else:
        season = "winter"
        weather_options = ["snow", "clear", "frost"]

    current_hour = dt.datetime.now().hour
    if 6 <= current_hour < 11:
        time_of_day = "morning"
    elif 11 <= current_hour < 18:
        time_of_day = "day"
    else:
        time_of_day = "night"

    background = f"{season}-{time_of_day}.png"
    weather_effect = random.choice(weather_options)

    return render_template(
        "index.html",
        pet=pet,
        pet_id=pet_id,
        pet_image=pet_image,
        background=background,
        weather_effect=weather_effect
    )

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

# ✅ Function to update pet stats every 2 hours
def update_pet_stats(pet_id):
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("SELECT * FROM pet WHERE pet_id=?", (pet_id,))
    pet = c.fetchone()

    if pet:  
        last_updated = dt.datetime.strptime(pet[9], "%Y-%m-%d %H:%M:%S")
        time_passed = dt.datetime.now() - last_updated

        if time_passed.total_seconds() >= 7200:  # 2 hours in seconds
            increments = int(time_passed.total_seconds() // 7200)
            new_hunger = min(10, pet[4] + increments)
            new_energy = max(0, pet[5] - increments)
            new_happiness = max(0, pet[6] - increments)
            new_health = max(0, pet[7] - increments)

            conn = sqlite3.connect("pet.db")
            c = conn.cursor()
            c.execute('''UPDATE pet SET hunger=?, energy=?, happiness=?, health=?, last_updated=? WHERE pet_id=?''',
                      (new_hunger, new_energy, new_happiness, new_health, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pet_id))
            conn.commit()
            conn.close()


# ✅ Interaction Route (Pet Actions)
@app.route("/interact", methods=["POST"])
def interact():
    pet_id = request.form.get("pet_id")
    action = request.form.get("action")

    print(f"🔍 Received pet_id: {pet_id}, action: {action}")  # Debugging

    if not pet_id:
        return jsonify({"error": "Missing pet_id"}), 400
    
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("SELECT hunger, energy, happiness, health FROM pet WHERE pet_id=?", (pet_id,))
    pet = c.fetchone()
    conn.close()

    if pet is None:
        return jsonify({"error": "Pet not found"}), 404

    # Extract values safely
    hunger, energy, happiness, health = map(lambda x: int(x) if x is not None else 5, pet)

    print(f"🔎 BEFORE UPDATE - Hunger: {hunger}, Energy: {energy}, Happiness: {happiness}, Health: {health}")

    # Apply action logic
    if action == "feed":
        hunger = min(10, hunger + 2)
    elif action == "play":
        happiness = min(10, happiness + 2)
        energy = max(0, energy - 1)  # Ensure energy doesn't go negative
    elif action == "rest":
        energy = min(10, energy + 2)
        health = min(10, health + 1)
    elif action == "heal":
        health = min(10, health + 3)

    print(f"✅ AFTER UPDATE - Hunger: {hunger}, Energy: {energy}, Happiness: {happiness}, Health: {health}")

    # Update the database
    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute("""
        UPDATE pet 
        SET hunger=?, energy=?, happiness=?, health=?, last_updated=? 
        WHERE pet_id=?
    """, (hunger, energy, happiness, health, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pet_id))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Pet stats updated",
        "hunger": hunger,
        "energy": energy,
        "happiness": happiness,
        "health": health
    }), 200

        
import random
import string

def generate_pet_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


# ✅ Save Moolapup Selection
@app.route("/save_moolapup", methods=["POST"])
def save_moolapup():
    name = request.form.get("name")
    color = request.form.get("color")

    print(f"DEBUG: Received selection - Name: {name}, Color: {color}")
    valid_colors = ["brown", "white", "black", "spotted"]
    if color not in valid_colors:
        return "Invalid color selection", 400

    pet_id = generate_pet_id()
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("pet.db")
    c = conn.cursor()
    c.execute('''INSERT INTO pet (pet_id, name, color, hunger, energy, happiness, health, last_updated)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (pet_id, name, color, 5, 5, 5, 5, now))
    conn.commit()
    conn.close()

    return redirect(url_for('home', pet_id=pet_id))



# ✅ Start Flask App
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)  # ✅ Required for Render
   

