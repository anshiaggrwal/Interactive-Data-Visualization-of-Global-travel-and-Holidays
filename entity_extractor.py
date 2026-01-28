#!/usr/bin/env python
# coding: utf-8

# In[7]:


import pandas as pd

data = pd.read_excel("E:\\ANSHI CLG\\frontend\\data\\Global Travel and Holidays.xlsx", sheet_name = None)
data.keys()


# In[8]:


holidays_df = data["Global Holidays"]
visits_from_df = data["country wise visits from india"]
international_visits_to_df = data["country wise visits to india"]
monthly_arrivals_df = data["Monthly arrival in India"]
monthly_fees_df = data["India's monthly fee in crore"]
receipts_df = data["International Tourism Receipts "]
international_departure_df = data["International visits from india"]
visitor_type_df = data["Monthly Arrival by Visitor Type"]
portwise_departures_df = data["PORT-WISE DEPARTURES OF INDIAN "]
top_places_df = data["Top Indian Places to Visit"]
cities_df = data["Cities to Visit in India"]


#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
from thefuzz import process
import re

SYNONYMS = {
    "dec": "december",
    "jan": "january",
    "nov": "november",
    "bombay": "mumbai",
    "goa's": "goa",
    "monsoons": "monsoon",
    "wintertime": "winter",
    "summertime": "summer",
}

SEASONS = ["summer", "winter", "monsoon", "spring", "autumn", "fall"]

MONTHS = ["january","february","march","april","may","june","july",
          "august","september","october","november","december"]

TIME_OF_DAY = ["morning", "afternoon", "evening", "night", "sunrise", "sunset"]

def clean_text(text):
    if text is None:
        return ""
    text = text.lower()
    for k, v in SYNONYMS.items():
        text = re.sub(r'\b' + re.escape(k) + r'\b', v, text)
    return text

STOP_WORDS = set(stopwords.words('english'))

def tokenize(text):
    text = clean_text(text)
    tokens = [t for t in word_tokenize(text) if t.isalpha() and t not in STOP_WORDS]
    return tokens

def fuzzy_match_token(token, choices, threshold=80):
    if not choices:
        return None
    res = process.extractOne(token, choices)
    if res:
        match, score = res[0], res[1] if isinstance(res, tuple) else res[1]
        if isinstance(res, tuple) and len(res) >= 2:
            match, score = res[0], res[1]
        else:
            try:
                match, score = res
            except Exception:
                return None
        return match if score >= threshold else None
    return None

def exact_in_text(candidate, text):
    return candidate in text

def extract_entities(text, category, holidays_df=None, top_places_df=None, 
                    cities_df=None, monthly_arrivals_df=None, 
                    receipts_df=None, visitor_type_df=None):
    text_org = "" if text is None else text
    text = clean_text(text_org)
    tokens = tokenize(text)
    entities = {}

    if category == "holiday details":
        # Month detection
        for t in tokens:
            m = fuzzy_match_token(t, MONTHS, threshold=80)
            if m:
                entities["month"] = m.title()
                break

        # Country detection
        if holidays_df is not None and "ADM_name" in holidays_df.columns:
            countries = holidays_df["ADM_name"].dropna().astype(str).str.lower().unique().tolist()
            
            # Token-based match
            for t in tokens:
                c = fuzzy_match_token(t, countries, threshold=80)
                if c:
                    entities["country"] = c.title()
                    break

            # Multi-word country match
            for c in countries:
                if exact_in_text(c, text):
                    entities["country"] = c.title()
                    break
        
        # Holiday type detection
        if holidays_df is not None and "Type" in holidays_df.columns:
            holiday_types = holidays_df["Type"].dropna().astype(str).str.lower().unique().tolist()

            for t in tokens:
                ht = fuzzy_match_token(t, holiday_types, threshold=80)
                if ht:
                    entities["holiday_type"] = ht.title()
                    break

            # Multi-word type match
            for ht in holiday_types:
                if exact_in_text(ht, text):
                    entities["holiday_type"] = ht.title()
                    break

        # Holiday name detection
        if holidays_df is not None and "Name" in holidays_df.columns:
            holiday_names = holidays_df["Name"].dropna().astype(str).str.lower().tolist()

            for name in holiday_names:
                if exact_in_text(name, text):
                    entities["holiday_name"] = name.title()
                    break

    elif category == "destination guidance":
        # PRIORITY 1: Specific Place Detection (highest priority)
        if top_places_df is not None and "Place" in top_places_df.columns:
            place_names = top_places_df["Place"].dropna().astype(str).str.lower().tolist()
            
            # First try exact multi-word match
            for place in place_names:
                if exact_in_text(place, text):
                    entities["place_name"] = place.title()
                    # Also extract the city for this place
                    place_row = top_places_df[top_places_df["Place"].str.lower() == place]
                    if not place_row.empty and "City" in place_row.columns:
                        city_val = place_row.iloc[0]["City"]
                        if pd.notna(city_val):
                            entities["city"] = str(city_val).title()
                    break
            
            # If no exact match, try fuzzy matching on tokens
            if "place_name" not in entities:
                for t in tokens:
                    p = fuzzy_match_token(t, place_names, threshold=75)
                    if p:
                        entities["place_name"] = p.title()
                        # Also extract the city
                        place_row = top_places_df[top_places_df["Place"].str.lower() == p.lower()]
                        if not place_row.empty and "City" in place_row.columns:
                            city_val = place_row.iloc[0]["City"]
                            if pd.notna(city_val):
                                entities["city"] = str(city_val).title()
                        break
        
        # PRIORITY 2: Time of day detection (before season/month)
        for t in tokens:
            tod = fuzzy_match_token(t, TIME_OF_DAY, threshold=80)
            if tod:
                entities["time_of_day"] = tod.title()
                break
        
        # PRIORITY 3: Season detection
        for t in tokens:
            s = fuzzy_match_token(t, SEASONS, threshold=80)
            if s:
                entities["season"] = s.title()
                break
        
        # PRIORITY 4: Month detection
        for t in tokens:
            m = fuzzy_match_token(t, MONTHS, threshold=80)
            if m:
                entities["month"] = m.title()
                break
        
        # PRIORITY 5: City detection (only if place_name not already found)
        if "place_name" not in entities:
            cities = []
            if cities_df is not None and "City" in cities_df.columns:
                cities += cities_df["City"].dropna().astype(str).str.lower().unique().tolist()
            if top_places_df is not None and "City" in top_places_df.columns:
                cities += top_places_df["City"].dropna().astype(str).str.lower().unique().tolist()
            cities = list(set(cities))

            # Token-based city match
            for t in tokens:
                c = fuzzy_match_token(t, cities, threshold=75)
                if c:
                    entities["city"] = c.title()
                    break
            
            # Multi-word city match
            if "city" not in entities:
                for city in cities:
                    if exact_in_text(city, text):
                        entities["city"] = city.title()
                        break

    elif category == "travel statistics":
        # Month detection
        for t in tokens:
            m = fuzzy_match_token(t, MONTHS, threshold=80)
            if m:
                entities["month"] = m.title()
                break

        # Year detection
        for t in tokens:
            if t.isdigit() and len(t) == 4:
                entities["year"] = t
                break

        # Country detection
        all_countries = []
        
        if visits_from_df is not None:
            country_cols = [c for c in visits_from_df.columns if "Country" in str(c)]
            if country_cols:
                all_countries += visits_from_df[country_cols[0]].dropna().astype(str).str.lower().unique().tolist()
        
        if international_visits_to_df is not None and "Country" in international_visits_to_df.columns:
            all_countries += international_visits_to_df["Country"].dropna().astype(str).str.lower().unique().tolist()

        all_countries = list(set(all_countries))

        for t in tokens:
            c = fuzzy_match_token(t, all_countries, threshold=75)
            if c:
                entities["country"] = c.title()
                break

        # Visitor type detection
        if visitor_type_df is not None and "Visitor Type" in visitor_type_df.columns:
            visitor_types = visitor_type_df["Visitor Type"].dropna().astype(str).str.lower().unique().tolist()
            for t in tokens:
                v = fuzzy_match_token(t, visitor_types, threshold=70)
                if v:
                    entities["visitor_type"] = v.title()
                    break

        # Season detection
        if "season" not in entities:
            for t in tokens:
                s = fuzzy_match_token(t, SEASONS, threshold=75)
                if s:
                    entities["season"] = s.title()
                    break

    if not entities:
        entities["none"] = True

    return entities