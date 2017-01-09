import _ from 'lodash';
import React, { Component } from 'react';
import Websocket from './websocket';
import AutoLinkText from 'react-autolink-text';
import ChatForm from './chat_form'
import { slugify, extractVideo } from './utils';


export default class Chat extends Component {

    constructor(props) {
        super(props);
        this.state = {
            messages: [],
            current: '',
        }
    }

    handleMessage(data) {
        console.log("RECEIVED: ", data);

        // NOTE: data should be an object of the form: {from: ..., message: ...}
        const new_message = {
            id: slugify(data.message) + new Date().valueOf(),  // ¯\_(ツ)_/¯
            text: data.message,
            from: data.from,
            avatar: data.from === "system" ? '' : data.avatar
        }
        const messages = _.concat(this.state.messages, [new_message]);
        this.setState({messages: messages, current: this.state.current});
    }

    onFormSubmit(event) {
        event.preventDefault();
        // event.target is the form.
        // event.target[0] is the first child element (our <input>)
        const inputElement = event.target.children[0].children[0];
        const message = inputElement.value;

        console.log("Sending?  ", message);

        this.setState({messages: this.state.messages, current: message});
        inputElement.value = ""; // clear the input.
    }

    renderMessageList() {
        // NOTE: Each object in our array of history looks like:
        // {
        //  created_on: "2017-01-05 21:57:39+0000"
        //  id:63
        //  read:false
        //  room:"chat-1-995"
        //  text:"Hi there"
        //  user:995
        //  user_full_name:"Brad Montgomery"
        //  user_username:"342ec11a7990133827bc6e66f381ee"
        // }

        // Make sure our history is sorted by date (oldest listed first).
        const historySorted = this.props.history.sort(function(a, b) {
            if(a.created_on < b.created_on) {
                return -1;
            }
            else if(a.created_on > b.created_on) {
                return 1;
            }
            // must be the same.
            return 0;
        })
        // then map the history attributes to those that we use to render new messages.
        const history = Array.from(historySorted, function(obj) {
            return {
                id: obj.id,
                text: obj.text,
                from: obj.user_full_name,
                avatar: '',
            }
        });

        // Combine the history with the current session's messages.
        const messages = history.concat(this.state.messages);

        const fullName = this.props.user.firstName + ' ' + this.props.user.lastName;
        return messages.map((msg) => {
            // A Reply is a message from the other user but not the system.
            const isReply = fullName !== msg.from && msg.from !== 'system';

            // Only show avatars for actual users.
            let avatar = '';
            if (this.props.user.avatar && !isReply && msg.from !== 'system') {
                avatar = <img src={this.props.user.avatar} className="avatar" role="presentation" />;
            }
            else if(msg.avatar && msg.from !== 'system') {
                avatar = <img src={msg.avatar} className="avatar" role="presentation" />;
            }
            const chatClasses = (isReply ? 'chatBubble reply' : 'chatBubble') +
                (msg.from === 'system' ? ' notice' : '');

            // Inline links to youtube videos, if applicable.
            const video = extractVideo(msg.text);
            let content = msg.text;
            if(video) {
                content = (
                    <div>
                        <div className={chatClasses}>
                            {avatar}
                            <AutoLinkText text={msg.text} />
                        </div>
                        <iframe width="640"
                                height="360"
                                src={video.embedUrl}
                                frameBorder="0" allowFullScreen />
                    </div>
                );
            }
            else {
                content = (
                    <div className={chatClasses}>
                        {avatar}
                        <AutoLinkText text={msg.text} />
                    </div>
                );
            }

            return (
                <li key={msg.id}>
                    {content}
                </li>
            );
        });
    }

    render() {
        return (
          <div className="chatContainer">
            <ul>{this.renderMessageList()}</ul>
            <Websocket url={this.props.ws_url}
                       debug={true}
                       onMessage={this.handleMessage.bind(this)}
                       sendMessage={this.state.current} />
            <ChatForm
                handleSubmit={this.onFormSubmit.bind(this)} />
          </div>
        );
    }
}
