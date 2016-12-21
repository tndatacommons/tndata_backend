import React from 'react';
import ReactDOM from 'react-dom';

import App from './components/app';



const rootEl = document.getElementById("root");
const apiToken = rootEl.getAttribute("data-token");

ReactDOM.render(
  <App apiToken={apiToken} />,
  rootEl
);
