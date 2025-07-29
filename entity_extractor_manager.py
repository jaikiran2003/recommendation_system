import re

def extract_entities(user_input: str) -> dict:
    entities = {}
    text = user_input.lower()

    seats_match = re.search(r"(\d+)\s*(seats|people|members)", text)
    if seats_match:
        entities["seats"] = int(seats_match.group(1))

    if "seats" not in entities and "family_size" not in entities:
        family_keywords = {
            "nuclear": 3,
            "small": 4,
            "medium": 5,
            "big": 6,
            "large": 7,
            "joint": 7,
        }
        for key, value in family_keywords.items():
            if key in text:
                entities["family_size"] = value
                break

    if "petrol" in text:
        entities["fuel_type"] = "Petrol"
    elif "diesel" in text:
        entities["fuel_type"] = "Diesel"
    elif "cng" in text:
        entities["fuel_type"] = "CNG"
    elif "electric" in text:
        entities["fuel_type"] = "Electric"

    if "automatic" in text:
        entities["transmission"] = "Automatic"
    elif "manual" in text:
        entities["transmission"] = "Manual"

    body_types = ["hatchback", "sedan", "suv", "mpv", "muv", "van", "crossover"]
    for body in body_types:
        if body in text:
            entities["car_type"] = body.capitalize()
            break

    if re.search(r"four[- ]?wheel|4wd", text):
        entities["drive_type"] = "Four Wheel Drive"
    elif re.search(r"rear[- ]?wheel", text):
        entities["drive_type"] = "Rear Wheel Drive"
    elif re.search(r"front[- ]?wheel", text):
        entities["drive_type"] = "Front Wheel Drive"

    range_match = re.search(
        r"(between|from)?\s*₹?\s*(\d+)\s*(lakh|lakhs)?\s*(to|and|-)\s*₹?\s*(\d+)\s*(lakh|lakhs)?", text
    )
    if range_match:
        lower = int(range_match.group(2)) * 100000
        upper = int(range_match.group(5)) * 100000
        entities["budget_min"] = lower
        entities["budget_max"] = upper
    else:
        max_match = re.search(r"(under|below|less than)\s*₹?\s*(\d+)\s*(lakh|lakhs)?", text)
        if max_match:
            entities["budget_max"] = int(max_match.group(2)) * 100000

        min_match = re.search(r"(above|over|more than)\s*₹?\s*(\d+)\s*(lakh|lakhs)?", text)
        if min_match:
            entities["budget_min"] = int(min_match.group(2)) * 100000

    mileage_above = re.search(r"(mileage\s*(above|over|more than))\s*(\d+)", text)
    if mileage_above:
        entities["arai_mileage_min"] = int(mileage_above.group(3))

    mileage_below = re.search(r"(mileage\s*(under|below|less than))\s*(\d+)", text)
    if mileage_below:
        entities["arai_mileage_max"] = int(mileage_below.group(3))

    mileage_range = re.search(r"mileage\s*(between|from)?\s*(\d+)\s*(to|and|-)\s*(\d+)", text)
    if mileage_range:
        entities["arai_mileage_min"] = int(mileage_range.group(2))
        entities["arai_mileage_max"] = int(mileage_range.group(4))

    return entities
