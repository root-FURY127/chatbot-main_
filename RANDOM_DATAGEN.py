import random
import string
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from faker import Faker

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment (fallback to localhost if not set)
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client["privacyguardian"]

# Clear existing collections (optional - comment out if you want to keep existing data)
db.users.drop()
db.data_locations.drop()
db.consents.drop()
print("Cleared existing collections.")

# Initialize Faker with Indian locale
fake = Faker('en_IN')

def generate_aadhaar():
    """Generate a random 12-digit Aadhaar number"""
    return ''.join([str(random.randint(0,9)) for _ in range(12)])

def generate_pan():
    """Generate a random PAN in format ABCDE1234F"""
    letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    last_letter = random.choice(string.ascii_uppercase)
    return letters + digits + last_letter

def generate_phone():
    """Generate Indian mobile number starting with 6-9, 10 digits"""
    first = str(random.randint(6,9))
    rest = ''.join([str(random.randint(0,9)) for _ in range(9)])
    return first + rest

def generate_email(name):
    """Generate email from name"""
    return name.lower().replace(' ', '.') + "@example.com"

# Generate 200 test users
users = []
for i in range(200):
    name = fake.name()
    email = generate_email(name)
    phone = generate_phone()
    aadhaar = generate_aadhaar()
    pan = generate_pan()
    address = fake.address().replace('\n', ', ')
    
    user = {
        "user_id": str(1000 + i),  # simple numeric ID
        "name": name,
        "email": email,
        "phone": phone,
        "aadhaar": aadhaar,
        "pan": pan,
        "address": address,
        "passport": None,  # optional
        "driving_license": None,
        "account_number": None
    }
    users.append(user)

# Insert users
result = db.users.insert_many(users)
print(f"Inserted {len(result.inserted_ids)} users.")

# For each user, create a data location entry (pointing to the MongoDB collection)
locations = []
for user in users:
    loc_entry = {
        "user_id": user["user_id"],
        "locations": [
            {
                "system": "MongoDB",
                "database": "privacyguardian",
                "collection": "users",
                "field": "aadhaar",
                "value": user["aadhaar"]
            },
            {
                "system": "MongoDB",
                "database": "privacyguardian",
                "collection": "users",
                "field": "pan",
                "value": user["pan"]
            },
            {
                "system": "MongoDB",
                "database": "privacyguardian",
                "collection": "users",
                "field": "phone",
                "value": user["phone"]
            },
            {
                "system": "MongoDB",
                "database": "privacyguardian",
                "collection": "users",
                "field": "email",
                "value": user["email"]
            }
        ],
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }
    locations.append(loc_entry)

# Insert data locations
db.data_locations.insert_many(locations)
print(f"Inserted {len(locations)} data location records.")

# Generate consents for each user
consents = []
for user in users:
    consent = {
        "user_id": user["user_id"],
        "purpose": "data_processing",
        "status": random.choice(["active", "active", "active", "withdrawn"]),  # 75% active
        "granted_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat() + "Z",
        "withdrawn_at": None
    }
    if consent["status"] == "withdrawn":
        consent["withdrawn_at"] = fake.date_time_between(start_date=consent["granted_at"], end_date="now").isoformat() + "Z"
    consents.append(consent)

db.consents.insert_many(consents)
print(f"Inserted {len(consents)} consent records.")

print("\nTest data population complete!")
print("Sample user IDs:", [u["user_id"] for u in users[:5]])