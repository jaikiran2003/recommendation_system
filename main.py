from entity_extractor_manager import extract_entities
from llm_handler import chat_with_phi, generate_sales_pitch, user_info, reset_conversation
from car_database import search_cars, get_car_by_name
import re

print("🚗 Welcome to Maruti Suzuki! I'm your personal car assistant.")

context = {}
last_mentioned_car = None
last_search_results = []  # To store last search results for recommendations

def normalize_context(ctx):
    normalized = {}

    if "budget_min" in ctx:
        normalized["budget_min"] = ctx["budget_min"]
    if "budget_max" in ctx:
        normalized["budget_max"] = ctx["budget_max"]
    if "car_type" in ctx:
        normalized["car_type"] = ctx["car_type"]
    if "fuel_type" in ctx:
        normalized["fuel_type"] = ctx["fuel_type"]
    if "drive_type" in ctx:
        normalized["drive_type"] = ctx["drive_type"]
    if "min_mileage" in ctx:
        normalized["min_mileage"] = ctx["min_mileage"]
    if "max_mileage" in ctx:
        normalized["max_mileage"] = ctx["max_mileage"]

    if "seats" in ctx:
        normalized["seats"] = ctx["seats"]
    elif "family_size" in ctx:
        normalized["seats"] = ctx["family_size"]

    return normalized

# Car model names (customizable based on your database)
possible_models = [
    "Dzire Tour", "Dzire", "Baleno", "Swift", "Alto", "Wagon R",
    "Brezza", "Fronx", "Eeco"
]

# Phrases that trigger a recommendation
RECOMMENDATION_TRIGGERS = [
    "which one", "recommend", "best", "suggest", "good one",
    "value", "better", "better option", "which is good",
    "top pick", "what should", "what would you", "choose",
    "go with", "prefer", "opinion", "which car"
]

# Irrelevant topics to detect
IRRELEVANT_TOPICS = [
    "bike", "motorcycle", "scooter", "bicycle", 
    "truck", "bus", "plane", "airplane",
    "boat", "ship", "train", "helicopter", "smartphones", "cosmetics", "mobiles"
]

def is_recommendation_request(text):
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in RECOMMENDATION_TRIGGERS)

def is_irrelevant_topic(text):
    text_lower = text.lower()
    return any(topic in text_lower for topic in IRRELEVANT_TOPICS)

def get_best_recommendation(cars):
    """Simple recommendation logic based on price and mileage"""
    if not cars:
        return None

    def score_car(car):
        try:
            mileage = float(re.findall(r"[\d.]+", car.get("ARAI_Certified_Mileage", "0"))[0])
            price = float(car.get("Ex-Showroom_Price_Value", 0))
            return mileage / price if price > 0 else 0
        except:
            return 0

    return max(cars, key=score_car)

# Start the conversation loop
while True:
    user_input = input("👤 You: ").strip()
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("🤖 Bot: Thanks for visiting Maruti Suzuki! Have a wonderful day ahead! 👋")
        break

    # First check for irrelevant topics
    if is_irrelevant_topic(user_input):
        print("🤖 Bot: I specialize in Maruti Suzuki cars. Please ask about our car models, features, or pricing!")
        continue

    # Handle recommendation requests if we have previous search results
    if last_search_results and is_recommendation_request(user_input):
        best_car = get_best_recommendation(last_search_results)
        if best_car:
            print(f"\n🤖 Bot: Based on your needs, I recommend the {best_car['Model']}:\n")
            pitch = generate_sales_pitch(best_car, comparison=True)
            print(f"🤖 Bot: {pitch}\n")
            continue

    # Step 1: Specific car model inquiry
    matched_model = next((model for model in possible_models if model.lower() in user_input.lower()), None)
    if matched_model:
        if matched_model != last_mentioned_car:
            car = get_car_by_name(matched_model)
            if car:
                print(f"\n🤖 Bot: Great choice! Let me tell you about the {car['Model']}:\n")
                pitch = generate_sales_pitch(car)
                print(f"🤖 Bot: {pitch}\n")
                print("🤖 Bot: Would you like to book a test drive, check EMI plans, or explore variants?\n")
                last_mentioned_car = matched_model
                continue
        else:
            print(f"🤖 Bot: Still considering the {matched_model}? It's a reliable pick! Let me know if you'd like details or comparisons.")
            continue

    # Step 2: Entity extraction for rule-based search
    entities = extract_entities(user_input)
    if entities:
        context.update(entities)

    normalized_context = normalize_context(context)

    has_min_criteria = any(k in normalized_context for k in [
        "seats", "budget_min", "budget_max", "fuel_type", "car_type",
        "drive_type", "min_mileage", "max_mileage"
    ])

    if has_min_criteria:
        results = search_cars(normalized_context)
        if results:
            last_search_results = results  
            print("\n🤖 Bot: Based on your preferences, here are some great Maruti Suzuki options:\n")
            for car in results:
                mileage = car.get("ARAI_Certified_Mileage_Value", None)
                mileage_display = f"{mileage} km/l" if isinstance(mileage, (int, float)) else "N/A km/l"
                print(f"- {car['Model']} | {car['Fuel_Type']} | {car['Seating_Capacity']} seats | {mileage_display} | ₹{car['Ex-Showroom_Price']}")
            print("\n🤖 Bot: Anything more on your mind? I can also recommend the best one for you!\n")
            continue
        else:
            print("🤖 Bot: Hmm, I couldn't find a perfect match. You might want to adjust your preferences a bit like budget or fuel type.\n")
            continue

    bot_reply = chat_with_phi(user_input)
    print(f"🤖 Bot: {bot_reply}")
