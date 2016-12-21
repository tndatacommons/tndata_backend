import React from 'react';
//import ReactDOM from 'react-dom';

/*
 * Adapted from:
 * https://github.com/mehmetkose/react-websocket/blob/master/index.jsx
 */

class Websocket extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
          ws: new WebSocket(this.props.url, this.props.protocol),
          attempts: 1,
          lastMessage: ''
        };

        this.send.bind(this);
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
          this.props.onMessage(evt.data);
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
        if(this.props.sendMessage && this.props.sendMessage !== this.state.lastMessage) {
            console.log("[Websocket.render], this.props = ", this.props);
            console.log("[Websocket.render], this.props.sendMessage = ", this.props.sendMessage);
            this.state.ws.send(this.props.sendMessage);
            this.setState({
                ws: this.state.ws,
                attempts: this.state.attempts,
                lastMessage: this.props.sendMessage
            })
        }
    }

    render() {
      // HACK: If we're getting re-rendered, it's possible some props/state
      // changed, so try to send any messages.
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
