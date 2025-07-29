class DialogueManager:
    def __init__(self):
        self.collected_info = {
            "family_size": None,
            "fuel_type": None,
            "price": None,
            "car_type": None,
        }

    def needs_more_info(self):
        return any(value is None for value in self.collected_info.values())

    def next_question(self):
        if self.collected_info["family_size"] is None:
            return "May I know how many members are in your family or who will usually be traveling in the car?"
        elif self.collected_info["fuel_type"] is None:
            return "Do you have a preference for fuel type — Petrol, Diesel, or CNG?"
        elif self.collected_info["price"] is None:
            return "And what's your approximate budget for the car?"
        elif self.collected_info["car_type"] is None:
            return "Finally, what kind of car do you want — hatchback, sedan, or SUV?"
        return None

    def update_info(self, new_data: dict):
        for key, value in new_data.items():
            if key in self.collected_info and value is not None:
                self.collected_info[key] = value
