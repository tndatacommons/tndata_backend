import React, { Component } from 'react';

import Chat from './chat';


const WS_HOST = 'ws://localhost:8000'


class App extends Component {
  render() {
    const ws_url = WS_HOST + window.location.pathname;

    return (
      <div className="App">
        <div className="App-header">
            <h1>Chat</h1>
        </div>
        <div className="App-content">
            <Chat ws_url={ws_url}/>
        </div>
      </div>
    );
  }
}

export default App;
