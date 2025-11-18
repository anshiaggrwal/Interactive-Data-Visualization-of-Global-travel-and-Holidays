import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
from entity_extractor import extract_entities

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

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

# Power BI Dashboard Links (UPDATE THESE WITH YOUR ACTUAL DASHBOARD LINKS)
DASHBOARD_LINKS = {
    "main": "https://app.powerbi.com/view?r=YOUR_MAIN_DASHBOARD_LINK",
    "arrivals": "https://app.powerbi.com/view?r=YOUR_ARRIVALS_DASHBOARD_LINK",
    "departures": "https://app.powerbi.com/view?r=YOUR_DEPARTURES_DASHBOARD_LINK",
    "tourism_receipts": "https://app.powerbi.com/view?r=YOUR_RECEIPTS_DASHBOARD_LINK",
}

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
    """Return formatted dashboard links"""
    return (
        f"📊 <b>Travel Statistics Dashboards</b><br><br>"
        f"For detailed statistical analysis and visualizations, please visit our interactive dashboards:<br><br>"
        f"🔹 <a href='{DASHBOARD_LINKS['main']}' target='_blank'><b>Main Tourism Dashboard</b></a><br>"
        f"   • Overall tourism trends and key metrics<br><br>"
        f"🔹 <a href='{DASHBOARD_LINKS['arrivals']}' target='_blank'><b>International Arrivals</b></a><br>"
        f"   • Monthly arrivals, visitor types, and country-wise data<br><br>"
        f"🔹 <a href='{DASHBOARD_LINKS['departures']}' target='_blank'><b>Indian Departures</b></a><br>"
        f"   • Port-wise departures and destination analysis<br><br>"
        f"🔹 <a href='{DASHBOARD_LINKS['tourism_receipts']}' target='_blank'><b>Tourism Receipts</b></a><br>"
        f"   • Revenue trends and financial analytics<br><br>"
        f"💡 <i>These dashboards provide interactive charts, filters, and detailed insights.</i>"
    )

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


# ---------------- FRONTEND SERVE ---------------------

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_file(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)