from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
import os
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder="templates") #flask application to know where to look for templates

# Cosmos DB connection details
COSMOS_ENDPOINT = os.getenv("DATABASE_URI")  # "Primary Connection String"
COSMOS_KEY = os.getenv("COSMOS_KEY")  # Primary Key in .env

# Ensuring that variables are loaded correctly
if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Missing required environment variables: DATABASE_URI and COSMOS_KEY")

# Initializing Cosmos Client
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

# Database and Container
DATABASE_NAME = "ProductDB"  
CONTAINER_NAME = "Products"  

database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER")

# Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER)


@app.route("/")
def home():
    return render_template("index.html") #index.html is rendered when homepage is opened

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

    # Uploading to Blob Storage
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file, overwrite=True)

    # Blob URL
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
        "image_url": data.get("image_url", "")  # image URL is stored in Cosmos DB
    }
    container.create_item(body=product)
    return jsonify({"message": "Product added successfully!"}), 201

#Route to list all products
@app.route("/products", methods=["GET"])
def get_products():
    products = list(container.read_all_items())  
    return jsonify(products)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Azure's default port
    app.run(debug=True, host="0.0.0.0", port=port)
