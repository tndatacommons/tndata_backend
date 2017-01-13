import React from 'react';
//import ReactDOM from 'react-dom';

/*
 * Adapted from:
 * https://github.com/mehmetkose/react-websocket/blob/master/index.jsx
 */

class Websocket extends React.Component {

    constructor(props) {
        super(props);
        this.send = this.send.bind(this);
        this.state = {
          ws: new WebSocket(this.props.url, this.props.protocol),
          attempts: 1,
        };
        this.lastMessage = '';
    }

    logging(logline) {
        if (this.props.debug === true) {
            console.log(logline);
        }
    }

    generateInterval (k) {
      return Math.min(30, (Math.pow(2, k) - 1)) * 1000;
    }

    setupWebsocket() {
        let websocket = this.state.ws;

        websocket.onopen = () => {
          this.logging('Websocket connected');
        };

        websocket.onmessage = (evt) => {
          // EXPECTED data format in json:  {from: ..., message: ...}
          this.logging("RECEIVED: " + evt.data)
          const data = JSON.parse(evt.data);
          this.props.onMessage(data);
        };

        this.shouldReconnect = this.props.reconnect;
        websocket.onclose = () => {
          this.logging('Websocket disconnected');

          if (this.shouldReconnect) {
            let time = this.generateInterval(this.state.attempts);
            setTimeout(() => {
              this.setState({attempts: this.state.attempts++});
              this.setupWebsocket();
            }, time);
          }
        }
    }


    componentDidMount() {
      this.setupWebsocket();
    }

    componentWillUnmount() {
      this.shouldReconnect = false;
      let websocket = this.state.ws;
      websocket.close();
    }

    send() {
        // Only send data if the websocket is open. See:
        // https://developer.mozilla.org/en-US/docs/Web/API/WebSocket#Constants
        if(this.state.ws.readyState === 1) {
            // This gets run during a render() because the message we want to send
            // changes on the props. We *can't* call `setState`, here, so we'll
            // just keep the last-sent message as an attribute on the class.
            //
            if(this.props.sendMessage && this.props.sendMessage !== this.lastMessage) {
                this.state.ws.send(this.props.sendMessage);
                this.lastMessage = this.props.sendMessage;
            }

            // Send read receipt if we have appropriate data.
            if(this.props.received) {
                this.state.ws.send(JSON.stringify({
                    received: this.props.received
                }));
            }
        }
    }

    render() {
      this.send();
      return (
        <div></div>
      );
    }
}

Websocket.defaultProps = {
    debug: false,
    reconnect: true
};

Websocket.propTypes = {
    url: React.PropTypes.string.isRequired,
    onMessage: React.PropTypes.func.isRequired,
    debug: React.PropTypes.bool,
    reconnect: React.PropTypes.bool,
    protocol: React.PropTypes.string
};

export default Websocket;
