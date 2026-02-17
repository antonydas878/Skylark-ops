from datetime import datetime

def date_overlap(a_start, a_end, b_start, b_end):
    return not (a_end < b_start or b_end < a_start)

def double_booking(pilot, mission):
    if not pilot["current_assignment"]:
        return False
    try:
        p_start = datetime.strptime(pilot["booked_from"], "%Y-%m-%d")
        p_end = datetime.strptime(pilot["booked_to"], "%Y-%m-%d")
        m_start = datetime.strptime(mission["start_date"], "%Y-%m-%d")
        m_end = datetime.strptime(mission["end_date"], "%Y-%m-%d")
        return date_overlap(p_start, p_end, m_start, m_end)
    except:
        return False

def weather_risk(drone, mission_weather):
    return mission_weather.lower() == "rainy" and drone["weather_rating"].lower() == "generic"

def maintenance_block(drone):
    return drone["status"].lower() == "maintenance"

def location_mismatch(pilot, drone):
    return pilot["location"].strip().lower() != drone["location"].strip().lower()
