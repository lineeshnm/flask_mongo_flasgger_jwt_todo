from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS 
from bson import ObjectId
import json
import jwt
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from functools import wraps
from flasgger import Swagger, swag_from
from pprint import pprint as pp

# Create an APISpec
template = {
  "swagger": "2.0",
  "info": {
    "title": "Flask Restful Swagger Demo",
    "description": "A Demof for the Flask-Restful Swagger Demo",
    "version": "0.1.1",
    "contact": {
      "name": "Kanoki",
      "url": "https://Kanoki.org",
    }
  },
  "securityDefinitions": {
    "Bearer": {
      "type": "apiKey",
      "name": "Authorization",
      "in": "header",
      "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\"",
      "bearerFormat": "JWT"
    }
  },
  "security": [
    {
      "Bearer": [ ]
    }
  ],
  "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "in": "header",
            }
        }
    }

}

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'My API',
    'uiversion': 3,
    "specs_route": "/swagger/"
}
swagger = Swagger(app, template= template)

CORS(app, resources={r"/*": {"origins": "*"}})
bcrypt = Bcrypt(app)
secret = "***************"

mongo = MongoClient('localhost', 27017)
db = mongo['py_api'] #py_api is the name of the db

def tokenReq(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        pp(request.headers)
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
            try:
                jwt.decode(token, secret)
            except:
                return jsonify({"status": "fail", "message": "No toekn in request unauthorized"}), 401
            return f(*args, **kwargs)
        else:
            return jsonify({"status": "fail", "message": "No Authorization in header unauthorized"}), 401
    return decorated

@app.route('/')
@swag_from('etc/home.yml')
def func():
    return "😺", 200

# get all and insert one
@app.route('/todos', methods=['GET', 'POST'])
@swag_from('etc/todos_post.yml', methods=['POST'])
@swag_from('etc/todos_get.yml', methods=['GET'])
def index():
    res = []
    code = 500
    status = "fail"
    message = ""
    try:
        if (request.method == 'POST'):
            res = db['todos'].insert_one(request.get_json())
            if res.acknowledged:
                message = "item saved"
                status = 'successful'
                code = 201
                res = {"_id": f"{res.inserted_id}"}
            else:
                message = "insert error"
                res = 'fail'
                code = 500
        else:
            for r in db['todos'].find().sort("_id", -1):
                r['_id'] = str(r['_id'])
                res.append(r)
            if res:
                message = "todos retrieved"
                status = 'successful'
                code = 200
            else:
                message = "no todos found"
                status = 'successful'
                code = 200
    except Exception as ee:
        res = {"error": str(ee)}
    return jsonify({"status":status,'data': res, "message":message}), code

# get one and update one
@app.route('/delete/<item_id>', methods=['DELETE'])
@swag_from('etc/delete_todo.yml', methods=['DELETE'])
@tokenReq
def delete_one(item_id):
    data = {}
    code = 500
    message = ""
    status = "fail"
    try:
        if (request.method == 'DELETE'):
            res = db['todos'].delete_one({"_id": ObjectId(item_id)})
            if res:
                message = "Delete successfully"
                status = "successful"
                code = 201
            else:
                message = "Delete failed"
                status = "fail"
                code = 404
        else:
            message = "Delete Method failed"
            status = "fail"
            code = 404
           
    except Exception as ee:
        message =  str(ee)
        status = "Error"

    return jsonify({"status": status, "message":message,'data': data}), code

# get one and update one
@app.route('/getone/<item_id>', methods=['GET', 'POST'])
@tokenReq
def by_id(item_id):
    data = {}
    code = 500
    message = ""
    status = "fail"
    try:
        if (request.method == 'POST'):
            res = db['todos'].update_one({"_id": ObjectId(item_id)}, { "$set": request.get_json()})
            if res:
                message = "updated successfully"
                status = "successful"
                code = 201
            else:
                message = "update failed"
                status = "fail"
                code = 404
        else:
            data =  db['todos'].find_one({"_id": ObjectId(item_id)})
            data['_id'] = str(data['_id'])
            if data:
                message = "item found"
                status = "successful"
                code = 200
            else:
                message = "update failed"
                status = "fail"
                code = 404
    except Exception as ee:
        message =  str(ee)
        status = "Error"

    return jsonify({"status": status, "message":message,'data': data}), code

@app.route('/signup', methods=['POST'])
@swag_from('etc/signup.yml')
def save_user():
    message = ""
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        check = db['users'].find({"email": data['email']})
        if check.count() >= 1:
            message = "user with that email exists"
            code = 401
            status = "fail"
        else:
            # hashing the password so it's not stored in the db as it was 
            data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
            data['created'] = datetime.now()

            #this is bad practice since the data is not being checked before insert
            res = db["users"].insert_one(data) 
            if res.acknowledged:
                status = "successful"
                message = "user created successfully"
                code = 201
    except Exception as ex:
        message = f"{ex}"
        status = "fail"
        code = 500
    return jsonify({'status': status, "message": message}), code

@app.route('/login', methods=['POST'])
@swag_from('etc/login.yml')
def login():
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        user = db['users'].find_one({"email": f'{data["email"]}'})

        if user:
            user['_id'] = str(user['_id'])
            if user and bcrypt.check_password_hash(user['password'], data['password']):
                time = datetime.utcnow() + timedelta(hours=24)
                token = jwt.encode({
                        "user": {
                            "email": f"{user['email']}",
                            "id": f"{user['_id']}",
                        },
                        "exp": time
                    },secret)

                del user['password']

                message = f"user authenticated"
                code = 200
                status = "successful"
                # print(token)
                res_data['token'] = token
                res_data['user'] = user

            else:
                message = "wrong password"
                code = 401
                status = "fail"
        else:
            message = "invalid login details"
            code = 401
            status = "fail"

    except Exception as ex:
        message = f"{ex}"
        code = 500
        status = "fail"
    return jsonify({'status': status, "data": res_data, "message":message}), code

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8000')