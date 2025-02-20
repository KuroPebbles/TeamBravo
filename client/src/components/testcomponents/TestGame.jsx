import React, {useState, useEffect} from "react";
import {useNavigate} from 'react-router-dom';
import socket from '../../socket';
import Camera from '../Camera';

//importing my own css styling because game page is broken
import './TestGame.css'


const TestGame = () => {
  const [usersInRoom, updateUsersInRoom] = useState([]);
  const [roomCode, updateRoomCode] = useState("");
  const [time, updateTime] = useState("0");
  const [gameState, updateGameState] = useState("waiting");
  const [item, updateItem] = useState("");
  const [input, updateInput] = useState("");

  const [showPopUp, updatePopUp] = useState(false);
  const [winner, updateWinner] = useState("");

  useEffect(() => {
    socket.emit('connect game');

    socket.on('room data', (data) => {
      console.log(data)
      // Extract current item
      if(data.items){
        updateItem(data.items);
      }
      // Extract time for room
      if(data.time){
        updateTime(data.time);
      }
      // Extract room code Data
      if(data.room_code){
        updateRoomCode(data.room_code);
      }
      // Extract game state
      if(data.game_state){
        updateGameState(data.game_state);
      }
      // Extract user data
      const users = {}
      Object.entries(data).forEach(([key,value]) => {
        if(key.startsWith("user:")) {
          const [, socketID, field] = key.split(":");
          if(!users[socketID]){
            users[socketID] = {};
          }
          users[socketID][field] = value;
        }
      })
      // convert user data to array
      const usersArray = Object.values(users);
      updateUsersInRoom(usersArray);
    })

    socket.on('start game', () => {
      updatePopUp(false);
    })

    socket.on('winner', (data) => {
      updatePopUp(true);
      updateWinner(data.message)
    })

    return () => {
      socket.emit('leave game');
    }
  },[])

  function startGame(){
    socket.emit('start game');
  }

  function endGame(){
    socket.emit('end game');
  }

  function changeInput(event){
    updateInput(event.target.value);
  }

  function submit(){
    socket.emit('submit', {submit:input});
    updateInput("");
  }

  return(
    <div className = "gameContainer">
      <div className = "gameBar">
        <h1>Test Game Page</h1>
        {gameState==="waiting" && (<div className="gameX"><h2>Time</h2><span>Game Hasn't started</span></div>)}
        {gameState==="running" && (<div className="gameX"><h2>Time{time}</h2><span>{time}</span></div>)}  
        {gameState==="waiting" && (<div className="gameX"><h2>Item</h2><span>None</span></div>)}
        {gameState==="running" && (<div className="gameX"><h2>Item</h2><span>{item}</span></div>)}  
      </div>
      <div className="gameSection">
        <div className="gameLeftPanel">
          <h2 class="gamePanelTitle">Connected Players:</h2>
          <ul>
            {usersInRoom.map((user, index) => (
                <li key={index}>
                  User:{user.username} Score:{user.score}
                </li>
            ))}
          </ul>
        </div>

        <div className="gameCamera">
          <Camera/>
        </div>
        
        <div className="gameRightPanel">
          <h2>GameState: {gameState}</h2>
          <h2>Room Code: {roomCode}</h2>
          {gameState==="waiting" && (<button onClick={startGame}>Start Game</button>)}
          {gameState==="running" && (<button onClick={endGame}>End Game</button>)}      
          <input onChange={changeInput} value={input} type="text" placeholder="Enter Item"></input>
          <button onClick={submit}>Submit</button>
          {showPopUp && (<div>{winner} wins!</div>)}
        </div>
      </div>
    </div>
  );

  
}


export default TestGame;