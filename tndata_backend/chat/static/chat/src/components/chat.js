import _ from 'lodash';
import React, { Component } from 'react';
import Websocket from './websocket';
//import Websocket from 'react-websocket';

/*
 * Stolen from:
 * https://gist.github.com/mathewbyrne/1280286
 *
 *
 * TODO: Read thru this, instead, & see if we should use something like it.
 * https://github.com/raineroviir/react-redux-socketio-chat/blob/master/src/common/containers/ChatContainer.js
 *
 *
 */
function slugify(text)
{
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')           // Replace spaces with -
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
    .replace(/\-\-+/g, '-')         // Replace multiple - with single -
    .replace(/^-+/, '')             // Trim - from start of text
    .replace(/-+$/, '');            // Trim - from end of text
}


export default class Chat extends Component {

    constructor(props) {
        super(props);
        this.state = {
            messages: [],
            current: '',
        }
        this.onFormSubmit.bind(this);
    }

    handleMessage(message) {
        const new_message = {
            id: slugify(message) + new Date().valueOf(),  // ¯\_(ツ)_/¯
            text: message
        }
        const messages = _.concat(this.state.messages, [new_message]);
        this.setState({messages: messages, current: this.state.current});
        console.log('[handleMessage], this.state.current = ', this.state.current);
    }

    onFormSubmit(event) {
        event.preventDefault();
        // event.target is the form.
        // event.target[0] is the first child element (our <input>)
        const message = event.target.children[0].value;
        console.log("[onFormSubmit] message = ", message);
        //this.handleMessage.bind(this)(message);

        this.setState({messages: this.state.messages, current: message});

        console.log('[onFormSubmit], this.state.current = ', this.state.current);
        event.target.children[0].value = ""; // clear the input.
    }

    render() {

        const messages = this.state.messages.map((msg) =>
            <li key={msg.id}>{msg.text}</li>
        );

        console.log('[render], this.state.current = ', this.state.current);
        return (
          <div>
            <ul>{messages}</ul>
            <Websocket url={this.props.ws_url}
                       debug={true}
                       onMessage={this.handleMessage.bind(this)}
                       sendMessage={this.state.current} />
            <form onSubmit={this.onFormSubmit.bind(this)}>
                <input type="text" name="message" />
                <button>Send</button>
            </form>
          </div>
        );
    }
}
