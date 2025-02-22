#Import Flask object
from flask import Flask, render_template, request
#import socket.io
from flask_socketio import SocketIO, join_room, leave_room, emit
import random
#for the purposes of threading
import threading
import time
import sqlite3

#flask constructor. Takes name as argument
app = Flask(__name__, template_folder='../client/dist', static_folder='../client/dist/assets')
app.config['SECRET_KEY'] = 'secret!'

# Initialize SocketIO
socketio = SocketIO(app)

#dictionary to track current online users
users = {}

#dictionary to track online users in rooms if we implement multiple rooms in the future
rooms = {}

#Items for game 
items = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
currItem = ""
global gameLength #number of items to go through
gameLength = 5 #for testing
global itemCount #current item count, will go to gameLength
itemCount = 0

#variables for game control
game_thread = None
is_game_running = False
game_lock = threading.Lock()
send_item_lock = threading.Lock()


@app.route('/', methods=['GET'])
def home():
  return render_template('index.html')

@app.route('/api/leaderboard', methods=['GET'])
def api_leaderboard():
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user, score FROM users ORDER BY score DESC LIMIT 4')
    rows = cursor.fetchall()
    conn.close()

    leaderboard = [{'Place': index + 1, 'Name': row[0], 'Score': row[1]} for index, row in enumerate(rows)]
    return {'leaderboard': leaderboard}, 200

@socketio.on('connect')
def hande_connection():
  print(f"A Client connected: {request.sid}")
  users[request.sid] = "Anonymous"


@socketio.on('client connection')
def handle_my_event(json):
  print('Received client connection: ' + str(json))
  emit('server acknowledge', {'data': 'Server acknowledged your connection'})

@socketio.on('username change')
def handle_username_change(data):
  users[request.sid] = data['data']

@socketio.on('start_timer')
def handle_start_timer(): #for rooms emit with room ID
  print('Timer started')
  emit('timer_started', broadcast=True)

@socketio.on('connect game')
def handle_connect_game():
  print(f"Client {request.sid}: {users[request.sid]} joined game room")

  join_room("Game room")

  if("Game room" not in rooms):
    rooms["Game room"] = []

  rooms["Game room"].append([request.sid, users[request.sid],0])

  emit('room data', rooms["Game room"],room = "Game room")

  start_game()

  emit('item data', currItem, room = "Game room")

@socketio.on('leave game')
def handle_disconnect_game():
  print(f"Client {request.sid}: {users[request.sid]} left game room")
  
  user_in_room = next((user for user in rooms["Game room"] if user[0] == request.sid), None)
  if user_in_room:
    saveScore(user_in_room[1], user_in_room[2])

  leave_room("Game room")

  #remove user from room if they go to a different page
  if("Game room" in rooms):
    rooms["Game room"] = [user for user in rooms["Game room"] if user[0] != request.sid]

    #stop game if no players left
    if(not rooms["Game room"]):
      end_game()
  emit('room data', rooms["Game room"],room = "Game room")

@socketio.on("disconnect")
def handle_disconnect():
  if(request.sid in users):
    
    #remove user from room if they go to a different page
    if("Game room" in rooms):
      rooms["Game room"] = [user for user in rooms["Game room"] if user[0] != request.sid]
      #stop game if no players left

      if not rooms["Game room"]:
        end_game()
    
    #remove users from users
    print(f"Client {request.sid}: {users[request.sid]} disconnected")
    del users[request.sid]

    emit('room data', rooms["Game room"],room = "Game room")

@socketio.on("check input")
def handle_check_input(data):
  if(not request.sid in users):
    return
  if(not "Game room" in rooms or not currItem):
    return
  
  #if data is equal to current item, increment score, otherwise give them a false response
  if(data == currItem):
    emit('server input res',{"response": "Correct"},room = "Game room")
    for user in rooms["Game room"]:
      if user[0] == request.sid:
        user[2] += 1
        break
    send_item()
  else:
    emit('server input res',{"Reponse": "Inccorrect"},room = "Game room")
  emit('room data', rooms["Game room"],room = "Game room")

#Game Logic
def send_item():
  global is_game_running
  global currItem
  global itemCount
  with send_item_lock:
    with game_lock:
      if "Game room" in rooms and is_game_running:
        if itemCount < gameLength:
          currItem = random.choice(items)
          itemCount += 1
          socketio.emit('item data', currItem)
        else:
          itemCount = 0
          emit('items complete')
          return 

def start_game():
  global is_game_running
  with game_lock:
      if(not is_game_running):
        print("Starting the game")
        is_game_running = True
        game_thread = threading.Thread(target=send_item, daemon=True)
        game_thread.start()
        emit('game started')

def end_game():
  global is_game_running
  with game_lock:
    if(is_game_running):
      print("Stopping the game")
      is_game_running = False
      emit('game ended')

def saveScore(user, score):
  #save score to database
  #for now just save scores later save to db instead
  print(f"User {user} scored {score}")

  conn = sqlite3.connect('scores.db')  # Connect to your database
  cursor = conn.cursor()
  # Create table if it doesn't exist
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user TEXT NOT NULL,
      score INTEGER NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  ''')

  # Insert score into the table
  cursor.execute('''
    INSERT INTO users (user, score)
    VALUES (?, ?)
  ''', (user, score))

  # Commit the transaction and close the connection
  conn.commit()
  conn.close()

def saveScores(gameRoom):
  for user in gameRoom:
    print(f"User {user[1]} scored {user[2]}")
    saveScore(user[1], user[2])

@socketio.on('game_over')
def handle_game_over():
  print("Game over")

  saveScores(rooms["Game room"])

if __name__ == '__main__':
  socketio.run(app, debug=True)
