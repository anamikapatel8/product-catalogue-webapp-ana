from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
import os
from azure.communication.email import EmailClient

from dotenv import load_dotenv
load_dotenv()

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

app = Flask(__name__, template_folder="templates") #flask to know where to look for templates

# Initialize Azure Communication Email Client
acs_connection_string = os.getenv("ACS_CONNECTION_STRING")
email_client = EmailClient.from_connection_string(acs_connection_string)

# Sender email (must be verified in Azure Communication Services)
sender_email = os.getenv("SENDER_EMAIL")

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

    # Send Email Notification
    send_email_notification(product)

    return jsonify({"message": "Product added successfully!"}), 201

#Route to list all products
@app.route("/products", methods=["GET"])
def get_products():
    products = list(container.read_all_items())  # Correct for Cosmos DB
    return jsonify(products)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use Azure's default port
    app.run(debug=True, host="0.0.0.0", port=port)

def send_email_notification(product):
    try:
        message = {
            "senderAddress": sender_email,
            "recipients": {
                "to": [{"address": "anamikapatel8@gmail.com"}]  # Change to recipient email
            },
            "content": {
                "subject": f"New Product Added: {product['name']}",
                "plainText": f"A new product '{product['name']}' has been added to the catalog.\n"
                             f"Category: {product['category']}\n"
                             f"Price: ${product['price']}\n"
                             f"Description: {product['description']}"
            }
        }
        poller = email_client.begin_send(message)
        result = poller.result()
        print("Email sent successfully!", result)
    except Exception as e:
        print(f"Error sending email: {e}")
