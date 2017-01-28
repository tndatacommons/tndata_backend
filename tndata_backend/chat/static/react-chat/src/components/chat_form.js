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
                <div className="input-group">
                    <input className="input-group-field"
                           type="text"
                           id="message"
                           name="message"
                           placeholder="Type your message, here."
                           ref={(input) => { this.inputField = input }} />
                    <div className="input-group-button">
                        <input type="submit" className="hollow button secondary" value="Send" />
                    </div>
                </div>
            </form>
        );
    }
}
