import React, { Component } from 'react';

import Chat from './chat';


// e.g. ==> ws://127.0.0.1:8000
const WS_HOST = 'ws://' + window.location.hostname + ':' + window.location.port


class App extends Component {
  render() {
    const ws_url = WS_HOST + window.location.pathname;
    console.log("[WEBSOCKET] " + ws_url);

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
