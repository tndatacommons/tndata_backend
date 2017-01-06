import _ from 'lodash';
import React, { Component } from 'react';
import ReactDOM from 'react-dom';


export default class ChatForm extends Component {

    /*
     * This method will scroll to the form into view every time it gets
     * re-rendered.
     */
    componentDidUpdate(prevProps) {
        const node = ReactDOM.findDOMNode(this.inputField);
        if(node) {
            node.scrollIntoView();
        }
    }

    render() {
        return (
            <form
                onSubmit={this.props.handleSubmit}
                className="chatForm">
              <div className="mdl-textfield mdl-js-textfield">
                <input className="mdl-textfield__input"
                       type="text"
                       id="message"
                       name="message"
                       ref={(input) => { this.inputField = input }} />
                <label className="mdl-textfield__label"
                       htmlFor="message">Your Message</label>
              </div>
              <button className="mdl-button mdl-js-button">Send</button>
            </form>
        );
    }
}
