import ollama
import re
from difflib import get_close_matches
from car_database import get_car_by_name, collection

context = [{
    "role": "system",
    "content": (
        "You are a Maruti Suzuki sales assistant. ONLY discuss real cars, prices, and features. "
        "Follow this workflow strictly:\n"
        "1. Greet the customer\n"
        "2. Ask about family size (seating needs)\n"
        "3. Ask fuel preference (Petrol/Diesel/CNG)\n"
        "4. Ask preferred car type (SUV/Sedan/Hatchback/MPV)\n"
        "5. Ask budget range\n"
        "6. Recommend suitable models\n\n"
        "RULES:\n"
        "- NEVER invent models, features, or prices\n"
        "- NEVER discuss hypothetical scenarios\n"
        "- All recommendations must be based on real Maruti Suzuki models\n"
        "- When asked for a recommendation, ALWAYS pick one specific model and justify your choice"
    )
}]

chat_history = context.copy()
user_info = {
    "family_size": None,
    "fuel_type": None,
    "car_type": None,
    "budget": None
}
last_recommended_cars = []

def is_off_topic(text):
    triggers = [
        "logic puzzle", "proof", "robot", "suv1", "tree of thought",
        "deduction", "logical reasoning", "imagine you", "customer a",
        "customer b", "hypothetical", "what if", "scenario",
        "thought experiment", "fictional", "pretend", "assume"
    ]
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in triggers)

def is_hallucination_response(text):
    red_flags = [
        "according to my calculations", "let me think through this",
        "here's a story", "imagine this", "suppose that", "theoretical",
        "abstract", "philosophical", "mathematical proof", "puzzle solution"
    ]
    return any(flag in text.lower() for flag in red_flags)

# === Entity Extractors ===
def extract_family_size(text):
    match = re.search(r'\b(\d+)\s*(people|members|family|persons|kids|adults)?\b', text.lower())
    return int(match.group(1)) if match else None

def extract_fuel_type(text):
    for fuel in ["petrol", "diesel", "cng"]:
        if fuel in text.lower():
            return fuel.capitalize()
    return None

def extract_budget(text):
    match = re.search(r'(\d+(?:\.\d+)?)\s*(lakh|lakhs|l|k|thousand)?', text.lower())
    if match:
        amount = float(match.group(1))
        unit = match.group(2)
        if unit:
            if "lakh" in unit or unit == "l":
                return int(amount * 100000)
            elif "k" in unit or "thousand" in unit:
                return int(amount * 1000)
        return int(amount)
    return None

def extract_car_type(text):
    for car_type in ["suv", "sedan", "hatchback", "mpv"]:
        if car_type in text.lower():
            return car_type.capitalize()
    return None

def get_recommendation_score(car, user_info):
    """Calculate a score for how well a car matches user preferences"""
    score = 0
    
    if user_info["budget"] and car.get("Ex-Showroom_Price_Value"):
        budget_diff = abs(user_info["budget"] - car["Ex-Showroom_Price_Value"])
        score += max(0, 100 - (budget_diff / user_info["budget"] * 100))
    
    if user_info["family_size"] and car.get("Seating_Capacity"):
        if car["Seating_Capacity"] >= user_info["family_size"]:
            score += 50
        else:
            score -= 100  
    
    try:
        mileage = float(re.findall(r"[\d.]+", car.get("ARAI_Certified_Mileage", "0"))[0])
        score += mileage * 2
    except:
        pass
    
    if car.get("Ex-Showroom_Price_Value"):
        score += car["Ex-Showroom_Price_Value"] / 100000  
    
    return score

# === Sales Pitch Generator ===
def generate_sales_pitch(car, comparison=False):
    try:
        model = car.get("Model", "this car")
        fuel = car.get("Fuel_Type", "Petrol")
        seats = car.get("Seating_Capacity", "5")
        mileage = car.get("ARAI_Certified_Mileage", "")
        price_value = car.get("Ex-Showroom_Price_Value")
        price_display = f"₹{price_value:,}" if price_value else car.get("Ex-Showroom_Price", "N/A")

        features = []

        # Add price-based value
        if price_value and price_value < 500000:
            features.append("very affordable and budget-friendly")
        elif price_value and price_value < 800000:
            features.append("great value for money")

        # Add mileage advantage
        if mileage:
            try:
                mileage_float = float(re.findall(r"[\d.]+", mileage)[0])
                if mileage_float >= 23:
                    features.append(f"excellent mileage of {mileage} – perfect for daily commuters")
                elif mileage_float >= 20:
                    features.append(f"good mileage of {mileage}")
            except:
                pass

        # Add usage-based suggestion
        if seats and int(seats) <= 5:
            features.append("ideal for small families or city driving")

        fuel_note = f"runs on {fuel}" if fuel.lower() != "petrol" else "offers a reliable petrol engine"

        # Compose pitch
        if comparison:
            pitch = f"🌟 My top recommendation is the Maruti Suzuki {model} because:\n"
        else:
            pitch = f"The Maruti Suzuki {model} is a smart choice! Here's why:\n"

        for feat in features:
            pitch += f"- {feat.capitalize()}\n"

        pitch += f"- Seats: {seats} | Fuel: {fuel}\n"
        pitch += f"- Priced at {price_display}\n"

        pitch += "\nWould you like to know more or book a test drive?"
        return pitch

    except Exception as e:
        return "Let me tell you about this model. Would you like to schedule a test drive?"

def chat_with_phi(user_message):
    global chat_history, user_info, last_recommended_cars

    lowered = user_message.lower()

    if is_off_topic(user_message):
        return "Let's focus on Maruti Suzuki cars. How can I help you find your perfect car today?"

    if not any(user_info.values()):
        if any(greet in lowered for greet in ["hi", "hello", "hey"]):
            return "Hello! Welcome to Maruti Suzuki. To help find your ideal car, how many people will usually be traveling with you?"

    if user_info["family_size"] is None:
        size = extract_family_size(user_message)
        if size:
            user_info["family_size"] = size
            return f"Thanks! For {size} people, we have great options. Do you prefer Petrol, Diesel, or CNG?"
        return "To recommend the right car, please tell me how many people will travel regularly?"

    if user_info["fuel_type"] is None:
        fuel = extract_fuel_type(user_message)
        if fuel:
            user_info["fuel_type"] = fuel
            return "Great choice! What type of car are you looking for? (SUV, Sedan, Hatchback, or MPV)"
        return "We offer Petrol, Diesel, and CNG options. Which do you prefer?"

    if user_info["car_type"] is None:
        car_type = extract_car_type(user_message)
        if car_type:
            user_info["car_type"] = car_type
            return f"Excellent! What's your approximate budget for the {car_type}?"
        return "We have SUVs, Sedans, Hatchbacks, and MPVs. Which type interests you?"

    if user_info["budget"] is None:
        budget = extract_budget(user_message)
        if budget:
            user_info["budget"] = budget
            query = {
                "Seating_Capacity": {"$gte": user_info["family_size"]},
                "Fuel_Type": user_info["fuel_type"].lower(),
                "Car_Type": user_info["car_type"].lower(),
                "Ex-Showroom_Price_Value": {"$lte": user_info["budget"] * 1.1}  # 10% flexibility
            }
            cars = list(collection.find(query).limit(6))
            if cars:
                last_recommended_cars = cars
                response = "🌟 Based on your needs, I recommend these models:\n"
                for car in cars:
                    response += f"- {car['Model']} | {car['Fuel_Type']} | {car['Seating_Capacity']} seats | {car.get('ARAI_Certified_Mileage', 'N/A')} | ₹{car['Ex-Showroom_Price_Value']:,}\n"
                response += "\nWould you like me to suggest the best option from these?"
                return response
            return "Let me check our inventory for suitable options. Could you adjust any preferences?"
        return "To suggest the best options, please share your approximate budget."

    recommendation_triggers = [
        "which one", "recommend", "best", "suggest", "good one", 
        "value", "better", "better option", "which is good", 
        "top pick", "what should", "what would you", "choose",
        "go with", "prefer", "opinion"
    ]
    
    if last_recommended_cars and any(trigger in lowered for trigger in recommendation_triggers):
        # Score and sort the cars
        scored_cars = [(car, get_recommendation_score(car, user_info)) for car in last_recommended_cars]
        scored_cars.sort(key=lambda x: x[1], reverse=True)
        
        if scored_cars:
            best_car = scored_cars[0][0]
            last_recommended_cars = []  # Clear to avoid repetition
            return generate_sales_pitch(best_car, comparison=True)

    # Handle "show me again" or "what were my options"
    if last_recommended_cars and ("options" in lowered or "show again" in lowered or "what were" in lowered):
        response = "Here are the models I recommended earlier:\n"
        for car in last_recommended_cars:
            response += f"- {car['Model']} | ₹{car['Ex-Showroom_Price_Value']:,}\n"
        response += "\nLet me know if you want know anything better?"
        return response

    # Handle specific variant queries
    variant_doc = collection.find_one({"Model_Variant": {"$regex": lowered, "$options": "i"}})
    if variant_doc:
        return generate_sales_pitch(variant_doc)

    # Fuzzy match for models
    words = re.findall(r"\b\w+\b", lowered)
    models_in_db = collection.distinct("Model")
    matched = get_close_matches(" ".join(words), models_in_db, n=1, cutoff=0.7)
    if matched:
        car = get_car_by_name(matched[0])
        if car:
            return generate_sales_pitch(car)

    # Fallback to LLM
    try:
        chat_history.append({"role": "user", "content": user_message})
        response = ollama.chat(
            model="phi",
            messages=chat_history,
            options={"temperature": 0.3, "repeat_penalty": 1.2}
        )
        bot_reply = response["message"]["content"]

        if is_hallucination_response(bot_reply) or is_off_topic(bot_reply):
            return "Let's focus on Maruti Suzuki cars. Would you like to know about models, pricing, or book a test drive?"

        chat_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    except Exception:
        return "I'm having trouble connecting. Please ask about Maruti Suzuki cars or visit our website."

# === Reset Conversation ===
def reset_conversation():
    global chat_history, user_info, last_recommended_cars
    chat_history = context.copy()
    user_info = {k: None for k in user_info}
    last_recommended_cars = []

# Explicitly expose
__all__ = ['chat_with_phi', 'generate_sales_pitch', 'user_info', 'reset_conversation']