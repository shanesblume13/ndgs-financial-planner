import json
import os

SCENARIO_FILE = "scenarios.json"

def load_scenarios():
    if os.path.exists(SCENARIO_FILE):
        with open(SCENARIO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_scenario(name, data):
    scenarios = load_scenarios()
    scenarios[name] = data
    with open(SCENARIO_FILE, "w") as f:
        json.dump(scenarios, f)
