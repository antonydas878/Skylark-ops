from datetime import datetime

def parse_list(s):
    return [x.strip().lower() for x in str(s).split(",")]

def skills_match(pilot_skills, required_skills):
    return set(parse_list(required_skills)).issubset(set(parse_list(pilot_skills)))

def certs_match(pilot_certs, required_certs):
    return set(parse_list(required_certs)).issubset(set(parse_list(pilot_certs)))

def location_match(pilot_loc, mission_loc):
    return pilot_loc.strip().lower() == mission_loc.strip().lower()

def calc_cost(daily_cost, start, end):
    days = (end - start).days + 1
    return int(daily_cost) * days
