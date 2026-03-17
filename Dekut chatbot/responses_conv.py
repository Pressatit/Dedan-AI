import json
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

with open(INTENTS_PATH, "r", encoding="utf-8") as f:
    intents_data = json.load(f)

intent_dict = {i["tag"]: i for i in intents_data["intents"]}

class IntentEngine:
    def __init__(self):
        with open("intents.json", "r") as f:
            data = json.load(f)
        self.intent_dict = {i["tag"]: i for i in data["intents"]}

    def get_response(self, tag):
        return random.choice(self.intent_dict[tag]["responses"])
    
