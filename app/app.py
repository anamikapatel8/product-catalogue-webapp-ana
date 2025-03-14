from flask import Flask, request, jsonify, render_template
from flask_pymongo import flask_pymongo
import os
from dotenv import load_dotenv

app = Flask(__name__)

#Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

#use the env variable for connection
app.config["MONGO_URI"] = os.getenv("DATABASE_URI")
mongo = PyMongo(app)

#Define the product collection
products_collection = mongo.db.products

@app.route("/")
def home():
    return "Welcome to the Product Catalogue Application 'ana'"


#Route to add a new product
@app.route("/add_product",methods=["POST"])

def add_product():
    data = request.get_json()
    product = {
        "name": data.get("name"),
        "description": data.get("description"),
        "price": data.get("price"),
        "category": data.get("category"),
        "stock": data.get("stock")
    }
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    result = products_collection.insert_one(product)
    return jsonify({"message": "Product added","id": str(result.inserted_id)})

#Route to list all products
@app.route("/products", methods=["GET"])
def get_products():
    products = list(products_collection.find({},{"_id": 0})) #Exclude objectId
    return jsonify(products)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
