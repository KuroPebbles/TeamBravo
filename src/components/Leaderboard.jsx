import React, { useEffect, useState, useRef } from 'react';
import {getLeaderboardData} from '../dataProvider.js';

const Leaderboard = props => {

    const [leaderboardData, setLeaderboardData] = useState([]);

    useEffect(() => {
        setLeaderboardData(getLeaderboardData());
    }, []);

    return (
        <div className='leaderboard'>
            <div className='leaderboard-title'>Leaderboard</div>
            <div className='leaderboard-players-container'>
            {
                leaderboardData.map(player =>
                    <div className='leaderboard-player-container' key={player.place}>
                        <span className='leaderboard-place'>{player.place}</span>
                        <span className='leaderboard-name'>{player.name}</span>
                        <span className='leaderboard-score'>{'score: ' + player.score}</span>
                    </div>
                )
            }
            </div>
        </div>
    )
}

export default Leaderboard