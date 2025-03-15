from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
import os
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename




from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder="templates") #flask to know where to look for templates

# Get Cosmos DB connection details
COSMOS_ENDPOINT = os.getenv("DATABASE_URI")  # This is your "Primary Connection String"
COSMOS_KEY = os.getenv("COSMOS_KEY")  # Store the Primary Key in .env

# Ensure variables are loaded correctly
if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Missing required environment variables: DATABASE_URI and COSMOS_KEY")

# Initialize Cosmos Client
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

# Get Database and Container
DATABASE_NAME = "ProductDB"  # Change to your actual database name
CONTAINER_NAME = "Products"  # Change to your actual container name

database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER")

# Initialize Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER)


@app.route("/")
def home():
    return render_template("index.html") #render index.html when homepage is opened
   # return "Welcome to the Product Catalogue Application 'ana'"

# Route to upload an image
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Secure filename
    filename = secure_filename(file.filename)

    # Upload to Blob Storage
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file, overwrite=True)

    # Get Blob URL
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{filename}"

    return jsonify({"message": "File uploaded successfully", "image_url": blob_url})



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
        "stock": data.get("stock"),
        "image_url": data.get("image_url", "")  # Store image URL in Cosmos DB
    }
    container.create_item(body=product)
    return jsonify({"message": "Product added successfully!"}), 201

#Route to list all products
@app.route("/products", methods=["GET"])
def get_products():
    products = list(container.read_all_items())  # Correct for Cosmos DB
    return jsonify(products)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use Azure's default port
    app.run(debug=True, host="0.0.0.0", port=port)
