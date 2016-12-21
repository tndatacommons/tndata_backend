import React, { Component } from 'react';

import Chat from './chat';


// Ensure our chat app hits the api running on the same host
// e.g. ==> ws://127.0.0.1:8000
//
// TODO: now to know if we're using port 8000, or 80, or 443 or what?
let PORT = window.location.port;
if(PORT.length > 0) {
    PORT = ":8000";
}
const WS_HOST = 'ws://' + window.location.hostname + PORT;


class App extends Component {
  render() {
    const ws_url = WS_HOST + window.location.pathname;
    console.log("[WEBSOCKET] " + ws_url);

    return (
      <div>
        <Chat ws_url={ws_url}/>
      </div>
    );
  }
}

export default App;
