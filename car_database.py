from pymongo import MongoClient

client = MongoClient("")
db = client[""]
collection = db[""]

def search_cars(filters: dict = {}, limit: int = None, debug: bool = False):
    """
    Search cars in the MongoDB collection based on given filters.
    Supports filtering by seats, price range, fuel type, drive type,
    car body type, model, and ARAI mileage.
    Returns a list of matching car documents up to the specified limit.
    """
    query = {}

    # Handle family_size by converting it to required seating capacity
    if "family_size" in filters:
        family_size = filters["family_size"]
        # Add 1 for the driver
        if isinstance(family_size, int):
            query["Seating_Capacity"] = {"$gte": family_size + 1}
        else:
            query["Seating_Capacity"] = {"$gte": 4}  # fallback default
    elif "seats" in filters:
        query["Seating_Capacity"] = {"$gte": filters["seats"]}

    if "budget_min" in filters and "budget_max" in filters:
        query["Ex-Showroom_Price_Value"] = {
            "$gte": filters["budget_min"],
            "$lte": filters["budget_max"]
        }
    elif "budget_min" in filters:
        query["Ex-Showroom_Price_Value"] = {"$gte": filters["budget_min"]}
    elif "budget_max" in filters:
        query["Ex-Showroom_Price_Value"] = {"$lte": filters["budget_max"]}

    if "fuel_type" in filters:
        query["Fuel_Type"] = {"$regex": filters["fuel_type"], "$options": "i"}

    if "drive_type" in filters:
        query["Drivetrain"] = {"$regex": filters["drive_type"], "$options": "i"}

    if "car_type" in filters:
        query["Body_Type"] = {"$regex": filters["car_type"], "$options": "i"}

    if "model" in filters:
        query["Model"] = {"$regex": filters["model"], "$options": "i"}

    if "min_mileage" in filters or "max_mileage" in filters:
        mileage_query = {}
        if "min_mileage" in filters:
            mileage_query["$gte"] = filters["min_mileage"]
        if "max_mileage" in filters:
            mileage_query["$lte"] = filters["max_mileage"]
        query["ARAI_Certified_Mileage_Value"] = mileage_query

    if debug:
        print("MongoDB Query:", query)

    cursor = collection.find(query)
    if limit is not None:
        cursor = cursor.limit(limit)

    results = list(cursor)
    if debug:
        print(f"Found {len(results)} results")

    return results


def get_car_by_name(name: str, debug: bool = False):
    """
    Retrieve a single car document matching the given model name.
    Case-insensitive partial match using regex.
    Returns None if no match is found.
    """
    query = {"Model": {"$regex": name, "$options": "i"}}
    if debug:
        print("MongoDB Query (by name):", query)
    return collection.find_one(query)
