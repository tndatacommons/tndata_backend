import React from 'react';
import ReactDOM from 'react-dom';
import App from './components/app';

// Read the user's auth token + the current room from the DOM.
const rootEl = document.getElementById("root");
const apiToken = rootEl.getAttribute("data-token");
const room = rootEl.getAttribute('data-room');

ReactDOM.render(
  <App apiToken={apiToken} room={room} />,
  rootEl
);


const debugEl = document.getElementById("extra-debug");
if(debugEl) {
    debugEl.innerHTML = "<p>Using token: " + apiToken + "</p>";
}

