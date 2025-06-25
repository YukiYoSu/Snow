# crew.py
import json
import os

CREW_FILE = "crews.json"

def load_crews():
    if not os.path.exists(CREW_FILE):
        return {}
    with open(CREW_FILE, "r") as f:
        return json.load(f)

def save_crews(crews):
    with open(CREW_FILE, "w") as f:
        json.dump(crews, f, indent=4)

def create_crew(user_id, crew_name):
    crews = load_crews()
    for crew in crews.values():
        if crew["name"].lower() == crew_name.lower():
            return False  # name already exists

    crews[str(user_id)] = {
        "name": crew_name,
        "captain": user_id,
        "members": [user_id],
        "points": 0
    }
    save_crews(crews)
    return True

def join_crew(user_id, crew_name):
    crews = load_crews()
    for crew in crews.values():
        if crew_name.lower() == crew["name"].lower():
            if user_id in crew["members"]:
                return "already"
            crew["members"].append(user_id)
            save_crews(crews)
            return "joined"
    return "not_found"

def leave_crew(user_id):
    crews = load_crews()
    to_delete = None

    for captain_id, crew in crews.items():
        if user_id in crew["members"]:
            crew["members"].remove(user_id)
            if user_id == crew["captain"]:
                if crew["members"]:
                    crew["captain"] = crew["members"][0]
                else:
                    to_delete = captain_id
            break

    if to_delete:
        del crews[to_delete]

    save_crews(crews)

def get_user_crew(user_id):
    crews = load_crews()
    for crew in crews.values():
        if user_id in crew["members"]:
            return crew
    return None

def get_all_crews():
    return load_crews().values()
