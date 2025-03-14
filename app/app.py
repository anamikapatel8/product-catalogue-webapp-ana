from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
import os


from dotenv import load_dotenv
load_dotenv()

# Get Cosmos DB connection details
COSMOS_ENDPOINT = os.getenv("DATABASE_URI")  # This is your "Primary Connection String"
COSMOS_KEY = os.getenv("COSMOS_KEY")  # Store the Primary Key in .env

# Initialize Cosmos Client
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

# Get Database and Container
DATABASE_NAME = "ProductDB"  # Change to your actual database name
CONTAINER_NAME = "Products"  # Change to your actual container name

database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

app = Flask(__name__, template_folder="../templates") #flask to know where to look for templates

@app.route("/")
def home():
    return render_template("index.html") #render index.html when homepage is opened
   # return "Welcome to the Product Catalogue Application 'ana'"


#Route to add a new product
@app.route("/add_product",methods=["POST"])

def add_product():
    data = request.get_json()
    if not data or "name" not in data or "price" not in data:
        return jsonify({"error": "Invalid input"}), 400

    product = {
        "id": str(data.get("name")), #'id' field is required by cosmosDB
        "name": data.get("name"),
        "description": data.get("description"),
        "price": data.get("price"),
        "category": data.get("category"),
        "stock": data.get("stock")
    }
    container.create_item(body=product)
    return jsonify({"message": "Product added successfully!"}), 201

#Route to list all products
@app.route("/products", methods=["GET"])
def get_products():
    products = list(container.read_all_items())  # Correct for Cosmos DB
    return jsonify(products)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
