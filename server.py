from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Access the MongoDB URI
mongo_uri = os.getenv("MONGO_URI")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize MongoDB connection
client = MongoClient(mongo_uri)
db = client["career_path"]
skills_collection = db["skills"]

# Fetch all skills (multi-word and single-word) from MongoDB
def get_valid_skills():
    skills = []
    cursor = skills_collection.find({})
    for document in cursor:
        skills.append(document['skill'])  # Assuming 'skill' contains the skill name
    return skills

# API route to analyze user skills
@app.route('/analyze', methods=['POST'])
def analyze_skills():
    data = request.json
    text = data.get('skills', '')

    # Pre-fetch valid skills from MongoDB
    valid_skills = get_valid_skills()

    # Normalize valid skills for case-insensitive matching
    normalized_valid_skills = {skill.lower(): skill for skill in valid_skills}

    # Extract skills from input text
    doc = nlp(text)
    extracted_skills = set()

    # Check for each skill in valid_skills directly in the input text
    for skill in normalized_valid_skills:
        if skill in text.lower():  # Case-insensitive match
            extracted_skills.add(normalized_valid_skills[skill])  # Add original-case skill name

    # Get career insights for extracted skills
    insights = {}
    for skill in extracted_skills:
        skill_info = skills_collection.find_one({"skill": {"$regex": f"^{skill}$", "$options": "i"}})
        if skill_info:
            insights[skill] = {
                "scope": skill_info.get("scope", "No scope data available"),
                "related_roles": skill_info.get("related_roles", ["No roles data available"]),
                "growth_rate": skill_info.get("growth_rate", "No growth rate data available"),
            }
        else:
            insights[skill] = "No data available"

    return jsonify(insights)

# Run the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
