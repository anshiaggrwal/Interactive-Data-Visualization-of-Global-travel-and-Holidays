import os
from flask import Flask, request, jsonify, send_from_directory, session, render_template_string
from flask_cors import CORS
import pandas as pd
import numpy as np
from entity_extractor import extract_entities
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import random, string
from datetime import datetime, timedelta
import pyotp  # pip install pyotp

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)
app.secret_key = 'my_travel_app_2025_super_secure_key_!@#9876543210xyz'


# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'sbad2005' 
app.config['MYSQL_DB'] = 'travel_app'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# Load your Excel file
EXCEL_PATH = "E:/Interactive Data Visualization of Global travel and Holidays/data/Global Travel and Holidays.xlsx"

try:
    excel_data = pd.read_excel(EXCEL_PATH, sheet_name=None)
except Exception as e:
    print("❌ Excel load error:", e)
    excel_data = {}

# Load sheets
holidays_df = excel_data.get("Global Holidays")
visits_from_df = excel_data.get("country wise visits from india")
international_visits_to_df = excel_data.get("country wise visits to india")
monthly_arrivals_df = excel_data.get("Monthly arrival in India")
visitor_type_df = excel_data.get("Monthly Arrival by Visitor Type")
top_places_df = excel_data.get("Top Indian Places to Visit")
cities_df = excel_data.get("Cities to Visit in India")


# ---------------- HELPERS ------------------

def pretty(text):
    return text.replace("\n", "<br>")

def format_holiday_row(r):
    return (
        f"🎉 <b>{r['Name']}</b><br>"
        f"📅 <b>Date:</b> {r['Date']}<br>"
        f"🌍 <b>Country:</b> {r['ADM_name']}<br>"
        f"🏷️ <b>Type:</b> {r['Type']}"
    )

def format_destination_row(r):
    desc = r.get("About the city (long Description)", "No description")
    best = r.get("Best Time to visit", "Not available")
    rating = r.get("Rating", "N/A")
    city = r.get("City", "Unknown")

    return (
        f"📍 <b>{city}</b><br>"
        f"⭐ Rating: {rating}<br>"
        f"🕐 Best Time: {best}<br>"
        f"ℹ️ {desc}"
    )

def format_place_row(r):
    """Format for specific places within cities"""
    place = r.get("Place", r.get("Name", "Unknown"))
    desc = r.get("About the Place", r.get("About the city (long Description)", "No description"))
    visit_time = r.get("Best Time to visit", "Anytime")
    rating = r.get("Rating", "N/A")
    city = r.get("City", "Unknown")

    return (
        f"🛕 <b>{place}</b> (in {city})<br>"
        f"⭐ Rating: {rating}<br>"
        f"🕐 Visit Time: {visit_time}<br>"
        f"ℹ️ {desc}"
    )

def format_dashboard_links():
    return "DASHBOARD_NAVIGATE_NOW"

# ---------------- CATEGORY HANDLERS -----------------

def holiday_details(entities):
    if holidays_df is None:
        return None, "Holiday dataset missing."

    df = holidays_df.copy()
    
    # Filter to show ONLY Public Holidays (exclude Observance and Local)
    if "Type" in df.columns:
        df = df[df["Type"].str.lower() == "public holiday"]

    if entities.get("country"):
        df = df[df["ADM_name"].str.lower() == entities["country"].lower()]

    if entities.get("month"):
        df = df[df["Month"].str.lower() == entities["month"].lower()]

    if df.empty:
        return None, "No public holidays found matching your criteria."

    return [format_holiday_row(r) for _, r in df.iterrows()], None


def destination_guidance(entities):
    results = []
    
    # PRIORITY 1: Specific place name mentioned (like "India Gate", "Miramar Beach")
    if entities.get("place_name"):
        place_name = entities["place_name"]
        
        if top_places_df is not None:
            df = top_places_df.copy()
            df = df[df["Place"].str.lower() == place_name.lower()]
            
            if not df.empty:
                for _, r in df.iterrows():
                    results.append(format_place_row(r))
                return results, None
            else:
                # Try partial match
                mask = df["Place"].str.lower().str.contains(place_name.lower(), na=False)
                df = df[mask]
                if not df.empty:
                    for _, r in df.iterrows():
                        results.append(format_place_row(r))
                    return results, None
    
    # PRIORITY 2: City mentioned - show places in that city
    if entities.get("city"):
        city_name = entities["city"]
        
        # If time_of_day is specified, filter by that
        if entities.get("time_of_day") and top_places_df is not None:
            df = top_places_df.copy()
            df = df[df["City"].str.lower() == city_name.lower()]
            
            time_of_day = entities["time_of_day"].lower()
            # Filter by visit time if available
            if "Best Time to visit" in df.columns:
                mask = df["Best Time to visit"].str.lower().str.contains(time_of_day, na=False)
                df = df[mask]
            
            if not df.empty:
                for _, r in df.head(5).iterrows():
                    results.append(format_place_row(r))
            
        # Show all places in the city
        if not results and top_places_df is not None:
            df = top_places_df.copy()
            df = df[df["City"].str.lower() == city_name.lower()]
            
            if not df.empty:
                for _, r in df.head(8).iterrows():
                    results.append(format_place_row(r))
        
        # Also add city overview
        if cities_df is not None:
            city_df = cities_df[cities_df["City"].str.lower() == city_name.lower()]
            for _, r in city_df.iterrows():
                results.append(format_destination_row(r))
        
        if results:
            return results, None

    # Helper function to check if a month falls within a date range
    def month_in_range(month_name, date_range_str):
        """Check if a month falls within 'October to March' type ranges"""
        if pd.isna(date_range_str) or not isinstance(date_range_str, str):
            return False
        
        date_range_str = date_range_str.lower()
        month_name = month_name.lower()
        
        # Check if month is directly mentioned
        if month_name in date_range_str:
            return True
        
        # Parse "Month to Month" ranges
        months_order = ["january", "february", "march", "april", "may", "june", 
                       "july", "august", "september", "october", "november", "december"]
        
        # Handle ranges like "October to March"
        if " to " in date_range_str:
            parts = date_range_str.split(" to ")
            if len(parts) == 2:
                start_month = parts[0].strip()
                end_month = parts[1].strip()
                
                try:
                    start_idx = next((i for i, m in enumerate(months_order) if m.startswith(start_month)), None)
                    end_idx = next((i for i, m in enumerate(months_order) if m.startswith(end_month)), None)
                    month_idx = next((i for i, m in enumerate(months_order) if m == month_name), None)
                    
                    if start_idx is not None and end_idx is not None and month_idx is not None:
                        # Handle wrap-around (e.g., October to March)
                        if start_idx <= end_idx:
                            return start_idx <= month_idx <= end_idx
                        else:
                            return month_idx >= start_idx or month_idx <= end_idx
                except:
                    pass
        
        return False

    # Helper function to check season match
    def season_matches(best_time_str, season_name):
        """Check if a season overlaps with the best time range"""
        if pd.isna(best_time_str) or not isinstance(best_time_str, str):
            return False
        
        best_time_str = best_time_str.lower()
        season_name = season_name.lower()
        
        # Define season months
        season_months = {
            "summer": ["march", "april", "may", "june"],
            "winter": ["november", "december", "january", "february"],
            "monsoon": ["june", "july", "august", "september"],
            "autumn": ["september", "october", "november"],
            "spring": ["march", "april", "may"]
        }
        
        if season_name in season_months:
            for month in season_months[season_name]:
                if month_in_range(month, best_time_str):
                    return True
        
        return False

    # PRIORITY 3: Season-based recommendations
    if entities.get("season") and cities_df is not None:
        df = cities_df.copy()
        mask = df["Best Time to visit"].apply(lambda x: season_matches(x, entities["season"]))
        df = df[mask]
        
        for _, r in df.head(5).iterrows():
            results.append(format_destination_row(r))

    # PRIORITY 4: Month-based recommendations
    if entities.get("month") and cities_df is not None:
        df = cities_df.copy()
        mask = df["Best Time to visit"].apply(lambda x: month_in_range(entities["month"], x))
        df = df[mask]
        
        for _, r in df.head(5).iterrows():
            results.append(format_destination_row(r))

    if not results:
        return None, "No matching destinations found. Try asking about:<br>• Specific places (e.g., 'India Gate', 'Taj Mahal', 'Marine Drive')<br>• Cities (e.g., 'Delhi', 'Mumbai', 'Goa')<br>• Seasons (e.g., 'summer', 'winter', 'monsoon')<br>• Months (e.g., 'January', 'December')"

    return results, None


def travel_statistics(entities):
    """Return Power BI dashboard links instead of raw data"""
    return [format_dashboard_links()], None


# ------------------- CHAT API -----------------------

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        query = data.get("query", "")
        category = data.get("category", "").lower()

        if not category:
            return jsonify({"ok": False, "message": "Category missing!"})

        entities = extract_entities(
            query,
            category,
            holidays_df=holidays_df,
            top_places_df=top_places_df,
            cities_df=cities_df,
            monthly_arrivals_df=monthly_arrivals_df,
            visitor_type_df=visitor_type_df,
        )

        if category == "holiday details":
            results, err = holiday_details(entities)

        elif category == "destination guidance":
            results, err = destination_guidance(entities)

        elif category == "travel statistics":
            results, err = travel_statistics(entities)

        else:
            return jsonify({"ok": False, "message": "Invalid category."})

        if err:
            return jsonify({"ok": False, "message": err})

        return jsonify({"ok": True, "results": results})
    
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"ok": False, "message": f"Server error: {str(e)}"})


# ---------- AUTH ----------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email').lower()
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({"ok": False, "message": "All fields required"})

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        return jsonify({"ok": False, "message": "Email already registered"})

    # THIS IS THE FIX: Properly hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        cur.execute("""INSERT INTO users (name, email, password) 
                       VALUES (%s, %s, %s)""", (name, email, hashed_password))
        mysql.connection.commit()
        return jsonify({"ok": True, "message": "Account created! Please login."})
    except Exception as e:
        return jsonify({"ok": False, "message": "Database error"})
    finally:
        cur.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email').lower()
    password = data.get('password')

    cur = mysql.connection.cursor()
    
    # GET USER + THEIR PERSONAL THEME IN ONE QUERY
    cur.execute("""
        SELECT id, name, password, COALESCE(theme, 'light') 
        FROM users 
        WHERE email = %s
    """, (email,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.check_password_hash(user[2], password):
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session['theme'] = user[3]  # This is their saved theme (light/dark)
        
        return jsonify({"ok": True, "name": user[1]})
    
    return jsonify({"ok": False, "message": "Invalid email or password"})

@app.route('/check-login')
def check_login():
    try:
        if 'user_id' not in session:
            return jsonify({"logged_in": False, "theme": "light"})
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT COALESCE(theme, 'light') FROM users WHERE id = %s", (session['user_id'],))
        result = cur.fetchone()
        theme = result[0] if result else 'light'
        cur.close()
        
        return jsonify({"logged_in": True, "theme": theme})
    except Exception as e:
        print(f"Check-login error: {e}")  # Log for debug
        return jsonify({"logged_in": False, "theme": "light"})  # Always valid JSON

@app.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.json['email'].lower()
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    if not user:
        return jsonify({"ok": False, "message": "Email not found"})
    
    otp = ''.join(random.choices(string.digits, k=6))
    session['otp'] = otp
    session['otp_time'] = datetime.now().timestamp()
    session['otp_email'] = email
    print(f"OTP for {email}: {otp}")  # In real app, send via email
    return jsonify({"ok": True, "message": "OTP sent to email"})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp = request.json['otp']
    if session.get('otp') == otp and (datetime.now().timestamp() - session.get('otp_time', 0)) < 300:
        email = session['otp_email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session.pop('otp', None)
        session.pop('otp_time', None)
        session.pop('otp_email', None)
        return jsonify({"ok": True, "name": user[1]})
    return jsonify({"ok": False, "message": "Invalid or expired OTP"})

# ---------- FEEDBACK ----------
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({"ok": False, "message": "Login required"})
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO feedback (user_id, type, message) VALUES (%s, %s, %s)",
                (session['user_id'], data['type'], data['message']))
    mysql.connection.commit()
    cur.close()
    return jsonify({"ok": True})

@app.route('/my-feedback')
def my_feedback():
    if 'user_id' not in session:
        return jsonify([])
    cur = mysql.connection.cursor()
    cur.execute("SELECT type, message, created_at FROM feedback WHERE user_id=%s ORDER BY created_at DESC", (session['user_id'],))
    feedback = cur.fetchall()
    cur.close()
    return jsonify([{"type": f[0], "message": f[1], "date": f[2].strftime("%b %d, %Y")} for f in feedback])

# ---------- SETTINGS ----------
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return jsonify({"ok": False})
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        data = request.json
        if 'theme' in data:
            cur.execute("UPDATE users SET theme=%s WHERE id=%s", (data['theme'], session['user_id']))
        if 'password' in data:
            hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
            cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, session['user_id']))
        mysql.connection.commit()
    cur.execute("SELECT name, email, theme FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    return jsonify({"name": user[0], "email": user[1], "theme": user[2]})

# ==================== SETTINGS: THEME & PASSWORD ====================
# SAVE THEME PER USER
@app.route('/settings/theme', methods=['POST'])
def save_theme():
    if 'user_id' not in session:
        return jsonify({"success": False})
    
    data = request.get_json()
    theme = data.get('theme', 'light')
    if theme not in ['light', 'dark']:
        theme = 'light'
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET theme = %s WHERE id = %s", (theme, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"success": True})


@app.route('/get-theme')
def get_theme():
    if 'user_id' not in session:
        return jsonify({"theme": "light"})
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT COALESCE(theme, 'light') FROM users WHERE id = %s", (session['user_id'],))
    theme = cur.fetchone()[0]
    cur.close()
    
    return jsonify({"theme": theme})

@app.route('/settings/password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({"ok": False, "message": "Login required"})
    
    data = request.json
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')
    
    if not all([old_pass, new_pass]):
        return jsonify({"ok": False, "message": "Both passwords required"})
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT password FROM users WHERE id = %s", (session['user_id'],))
    current_hash = cur.fetchone()[0]
    
    if not bcrypt.check_password_hash(current_hash, old_pass):
        cur.close()
        return jsonify({"ok": False, "message": "Current password is wrong"})
    
    new_hash = bcrypt.generate_password_hash(new_pass).decode('utf-8')
    cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_hash, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"ok": True, "message": "Password changed successfully!"})

# ---------------- FRONTEND SERVE ---------------------

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_file(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)