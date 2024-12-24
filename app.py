from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo import ReturnDocument

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongo:27017/clients_db"
mongo = PyMongo(app)

def get_next_client_id():
    sequence = mongo.db.clients.find_one({"_id": "client_id_sequence"})
    if sequence is None:
        mongo.db.clients.insert_one({"_id": "client_id_sequence", "seq_value": -1})
    client = mongo.db.clients.find_one_and_update(
        {"_id": "client_id_sequence"},
        {'$inc': {'seq_value': 1}},
        projection={'seq_value': True, '_id': False},
        return_document=ReturnDocument.AFTER
    )
    return client['seq_value']


def get_next_product_id():
    sequence = mongo.db.products.find_one({"_id": "product_id_sequence"})
    if sequence is None:
        mongo.db.products.insert_one({"_id": "product_id_sequence", "seq_value": -1})
    product = mongo.db.products.find_one_and_update(
        {"_id": "product_id_sequence"},
        {'$inc': {'seq_value': 1}},
        projection={'seq_value': True, '_id': False},
        return_document=ReturnDocument.AFTER
    )
    return product['seq_value']


def get_next_order_id():
    sequence = mongo.db.orders.find_one({"_id": "order_id_sequence"})
    if sequence is None:
        mongo.db.orders.insert_one({"_id": "order_id_sequence", "seq_value": -1})
    order = mongo.db.orders.find_one_and_update(
        {"_id": "order_id_sequence"},
        {'$inc': {'seq_value': 1}},
        projection={'seq_value': True, '_id': False},
        return_document=ReturnDocument.AFTER
    )
    return order['seq_value']


#--------------------------------------------------------------------------------
@app.route('/clients', methods=['PUT'])
def create_client():
    data = request.get_json()
    client_id = data.get("id")
    name = data.get("name")
    email = data.get("email")
    
    if not name or not email:
        return jsonify({"message": "Invalid input, missing name or email"}), 400

    if client_id and client_id.isdigit():
        client_id = f"client_{client_id}"
    else:
        client_id = get_next_client_id()
        client_id = f"client_{client_id}"

    client_data = {
        'id': client_id,
        'name': name,
        'email': email
    }
    
    mongo.db.clients.insert_one(client_data)

    return jsonify({"id": client_id.split('_')[1]}), 201

#--------------------------------------------------------------------------------
@app.route('/clients/<clientId>', methods=['GET'])
def get_client(clientId):
    if clientId.isdigit():
        client_id_str = f"client_{clientId}"
    else:
        client_id_str = clientId

    client = mongo.db.clients.find_one({'id': client_id_str})

    if not client:
        return jsonify({"message": "Client not found"}), 404

    client_data = {
        'id': client.get('id').split('_')[1] if client.get('id').startswith('client_') else client.get('id'),
        'name': client.get('name'),
        'email': client.get('email')
    }
    return jsonify(client_data), 200




#--------------------------------------------------------------------------------
@app.route('/clients/<clientId>', methods=['DELETE'])
def delete_client(clientId):
    client_id_str = f"client_{clientId}" if clientId.isdigit() else clientId

    client = mongo.db.clients.find_one({'id': client_id_str})
    if client is None:
        return jsonify({"message": "Client not found"}), 404

    mongo.db.clients.delete_one({'id': client_id_str})
    mongo.db.orders.delete_many({'client_id': client_id_str})

    mongo.db.reviews.delete_many({'client_id': client_id_str})

    mongo.db.subscriptions.delete_many({'client_id': client_id_str})
    mongo.db.notifications.delete_many({'client_id': client_id_str})

    return jsonify({"message": "Client and all associated data deleted"}), 204

#--------------------------------------------------------------------------------
@app.route('/products', methods=['PUT'])
def create_product():
    try:
        data = request.get_json()
        product_id = data.get("id")
        name = data.get("name")
        category = data.get("category")
        price = data.get("price")

        if not name or price is None:
            return jsonify({"message": "Invalid input, missing name or price"}), 400

        if not product_id:
            product_id = get_next_product_id()
            product_id = f"product_{product_id}"


        product_data = {
            'id': product_id,
            'name': name,
            'category': category,
            'price': price
        }

        mongo.db.products.insert_one(product_data)
        return jsonify({"id": product_id.split('_')[1] if product_id.startswith('product_') else product_id}), 201

    except Exception as e:
        return jsonify({"message": "Error occurred", "error": str(e)}), 500

#--------------------------------------------------------------------------------
@app.route('/products', methods=['GET'])
def get_all_products():
    try:
        category = request.args.get('category')

        if category:
            products = mongo.db.products.find({'category': category}, {'_id': 0, 'id': 1, 'name': 1, 'category': 1, 'price': 1})
        else:
            products = mongo.db.products.find({}, {'_id': 0, 'id': 1, 'name': 1, 'category': 1, 'price': 1})

        product_list = []
        for product in products:
            if 'id' not in product:
                print(f"Product without 'id': {product}")
                continue

            if product['id'].startswith('product_'):
                product_id = product['id'].split('_')[1]
            else:
                product_id = product['id']

            product_list.append({
                'id': product_id,
                'name': product['name'],
                'category': product['category'],
                'price': product['price']
            })

        return jsonify(product_list), 200

    except Exception as e:
        return jsonify({"message": "Error occurred", "error": str(e)}), 500

#--------------------------------------------------------------------------------
@app.route('/products/<productId>', methods=['GET'])
def get_product(productId):
    product = mongo.db.products.find_one({'id': productId})
    
    if product is None:
        return jsonify({"message": "Product not found"}), 404
    
    product_data = {
        'id': product['id'].split('_')[1] if product['id'].startswith('product_') else product['id'],
        'name': product['name'],
        'category': product['category'],
        'description': product.get('description', 'string'),
        'price': product['price']
    }
    return jsonify(product_data), 200
#--------------------------------------------------------------------------------
@app.route('/products/<productId>', methods=['DELETE'])
def delete_product(productId):
    product = mongo.db.products.find_one({'id': productId})
    
    if product is None:
        return jsonify({"message": "Product not found"}), 404

    mongo.db.products.delete_one({'id': productId})

    mongo.db.orders.update_many(
        {'products': {'$elemMatch': {'id': productId}}},
        {'$pull': {'products': {'id': productId}}}
    )

    mongo.db.inventory.delete_many({'product_id': productId})

    return jsonify({"message": "Product and all related information deleted"}), 200


#--------------------------------------------------------------------------------
@app.route('/orders', methods=['PUT'])
def create_order():
    data = request.get_json()
    
    if not isinstance(data.get('clientId'), str) or not isinstance(data.get('items'), list) or not data['items']:
        return jsonify({"message": "Invalid input, 'clientId' must be a string and 'items' must be a non-empty array"}), 400

    client_id = f"client_{data['clientId']}"  
    client = mongo.db.clients.find_one({'id': client_id})
    
    if client is None:
        return jsonify({"message": "Client not found"}), 404

    items_with_details = []
    total_price = 0.0

    for item in data['items']:
        if not isinstance(item.get('productId'), str) or not isinstance(item.get('quantity'), int) or item['quantity'] <= 0:
            return jsonify({"message": "Invalid item format: 'productId' must be a string and 'quantity' must be a positive integer"}), 400

        product_id = item['productId']
        print(f"Looking for product with ID: {product_id}")

        product = mongo.db.products.find_one({'id': product_id})

        if product is None:
            return jsonify({"message": f"Product with ID {item['productId']} not found"}), 404
        
        item_total = product['price'] * item['quantity']
        total_price += item_total
        
        items_with_details.append({
            'productId': item['productId'],
            'quantity': item['quantity'],
            'unitPrice': product['price'],
            'totalPrice': item_total
        })

    order_id = get_next_order_id()
    order = {
        'id': f"order_{order_id}",
        'client_id': client_id,
        'items': items_with_details,
        'total_price': total_price
    }

    mongo.db.orders.insert_one(order)

    return jsonify({"id": str(order_id)}), 201



#--------------------------------------------------------------------------------
@app.route('/clients/<clientId>/orders', methods=['GET'])
def get_client_orders(clientId):
    client_id = f"client_{clientId}"

    orders = mongo.db.orders.find({'client_id': client_id})
    order_list = []

    for order in orders:
        order_data = {
            'id': order['id'],
            'items': order['items'],
            'total_price': order['total_price']
        }
        order_list.append(order_data)

    if order_list:
        return jsonify({"message": "List of orders for client", "orders": order_list}), 200
    else:
        return jsonify({"message": "No orders found for this client"}), 404


#--------------------------------------------------------------------------------
@app.route('/statistics/top/clients', methods=['GET'])
def get_top_clients():
    pipeline = [
        {"$match": {"client_id": {"$ne": None}}},
        {"$group": {"_id": "$client_id", "totalOrders": {"$sum": 1}}},
        {"$lookup": {
            "from": "clients",
            "localField": "_id",
            "foreignField": "id",
            "as": "clientDetails"
        }},
        {"$unwind": {
            "path": "$clientDetails",
            "preserveNullAndEmptyArrays": True
        }},
        {"$project": {
            "_id": 0,
            "id": {"$ifNull": ["$clientDetails.id", ""]},
            "name": {"$ifNull": ["$clientDetails.name", "Unknown"]},
            "totalOrders": 1
        }},
        {"$match": {"id": {"$ne": ""}}},
        {"$sort": {"totalOrders": -1}},
        {"$limit": 10}
    ]
    top_clients = list(mongo.db.orders.aggregate(pipeline))
    return jsonify({"clients": top_clients}), 200
#--------------------------------------------------------------------------------
@app.route('/statistics/top/products', methods=['GET'])
def get_top_products():
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.productId", "quantity": {"$sum": "$items.quantity"}}},
        {"$lookup": {
            "from": "products",
            "localField": "_id",
            "foreignField": "id",
            "as": "productDetails"
        }},
        {"$unwind": {
            "path": "$productDetails",
            "preserveNullAndEmptyArrays": True
        }},
        {"$project": {
            "productId": {"$toString": "$_id"},
            "name": {"$ifNull": ["$productDetails.name", "Unknown"]},
            "quantity": 1
        }},
        {"$sort": {"quantity": -1}},
        {"$limit": 10}
    ]
    top_products = list(mongo.db.orders.aggregate(pipeline))
    return jsonify({"message": "Top products", "products": top_products}), 200


#--------------------------------------------------------------------------------
@app.route('/statistics/orders/total', methods=['GET'])
def get_total_orders():
    total_orders = mongo.db.orders.count_documents({})
    return jsonify({"message": "Total number of orders", "total": total_orders}), 200

#--------------------------------------------------------------------------------
@app.route('/statistics/orders/totalValue', methods=['GET'])
def get_total_order_value():
    pipeline = [
        {"$group": {"_id": None, "totalValue": {"$sum": "$total_price"}}}
    ]
    total_value = list(mongo.db.orders.aggregate(pipeline))
    total_value = total_value[0]['totalValue'] if total_value else 0
    return jsonify({"message": "Total value of orders", "totalValue": total_value}), 200


#--------------------------------------------------------------------------------
@app.route('/cleanup', methods=['POST'])
def delete_all_data():
    mongo.db.clients.delete_many({})
    mongo.db.products.delete_many({})
    mongo.db.orders.delete_many({})
    return '', 204
#--------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
