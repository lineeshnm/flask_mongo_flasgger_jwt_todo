# flask_mongo_flasgger_jwt_todo

1. Enable change stream on MongoDB - not necessory
2. intialize replica set

3. Create socket in server. 
from flask_socketio import SocketIO, emit, Namespace
socketio = SocketIO(app, cors_allowed_origins="*")
class MyCustomNamespace(Namespace):
    def on_connect(self):
        print("Client just connected")

    def on_disconnect(self):
        print("Client just left")

socketio.on(MyCustomNamespace('/socket'))

4. On update, delete, create emit a message to all clients. 
socketio.emit('data_refesh', namespace='/socket')
5. Client side: Wait for message via socket and if message received, fetch the data  only on the notification page. 
import io from "socket.io-client";
  componentDidMount = async () => {
    //socket.io connection
    // const socket = io(`${URLs.socketURL}/socket`);
    const socket = io(`localhost:8000/socket`);
    socket.on("data_refesh", () => {
      console.log("A new braodcast message received")
	  fetchData()
    })

Some sample to test the mongoDB
export CHANGE_STREAM_DB="mongodb://localhost:27017/changeSteam?retryWrites=true"

import os
import pymongo
client = pymongo.MongoClient(os.environ['CHANGE_STREAM_DB'])
print(client.changestream.collection.insert_one({"hello": "world"}).inserted_id)

import os
import pymongo
from bson.json_util import dumps

client = pymongo.MongoClient(os.environ['CHANGE_STREAM_DB'])
change_stream = client.changestream.collection.watch()
for change in change_stream:
    print(dumps(change))
    print('') # for readability only
	