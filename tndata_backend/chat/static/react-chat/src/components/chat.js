import _ from 'lodash';
import React, { Component } from 'react';
import Websocket from './websocket';
import AutoLinkText from 'react-autolink-text';

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

/*
 * If the given text contains a link to a youtube video, this function
 * will parse the text and extract two bits of data:
 *
 * 1. The video URL, and
 * 2. The video ID.
 *
 * If matched, this function returns an object of the form:
 *
 *  {
 *      videoId: '...',
 *      embedUrl: '...',
 *  }
 *
 * Otherwise, it returns a false value.
 *
 * This current works for both short, and long share urls:
 * - https://www.youtube.com/watch?v=fd6clpIvrfg
 * - https://youtu.be/fd6clpIvrfg
 */
function extractVideo(text) {
    let result = false;
    let videoId = null;
    let videoLink = null;
    const short_re = /https:\/\/youtu.be\/(\w+)/;
    const long_re = /https:\/\/www.youtube.com\/watch\?v=(\w+)/;

    if(short_re.test(text)) {
        // Note: returns ["https://youtu.be/fd6clpIvrfg", "fd6clpIvrfg"]
        [videoLink, videoId] = short_re.exec(text);
        result = {
            videoId: videoId,
            videoLink: videoLink,
            embedUrl: "https://www.youtube.com/embed/" + videoId
        }
    }
    else if(long_re.test(text)) {
        [videoLink, videoId] = long_re.exec(text);
        result = {
            videoId: videoId,
            videoLink: videoLink,
            embedUrl: "https://www.youtube.com/embed/" + videoId
        }
    }
    console.log("Video Extraction result: ", result);
    return result;
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

    handleMessage(data) {
        // NOTE: data should be an object of the form: {from: ..., message: ...}
        const new_message = {
            id: slugify(data.message) + new Date().valueOf(),  // ¯\_(ツ)_/¯
            text: data.message,
            from: data.from
        }
        const messages = _.concat(this.state.messages, [new_message]);
        this.setState({messages: messages, current: this.state.current});
        console.log('[handleMessage], this.state.current = ', this.state.current);
    }

    onFormSubmit(event) {
        event.preventDefault();
        // event.target is the form.
        // event.target[0] is the first child element (our <input>)
        const inputElement = event.target.children[0].children[0];
        const message = inputElement.value;
        console.log("[onFormSubmit] message = ", message);

        this.setState({messages: this.state.messages, current: message});

        console.log('[onFormSubmit], this.state.current = ', this.state.current);
        inputElement.value = ""; // clear the input.
    }

    renderMessageList() {
        return this.state.messages.map((msg) => {
            // A Reply is a message from the other user but not the system.
            const isReply = this.props.user.username !== msg.from && msg.from !== 'system';

            // Dont' show avatars for system messages.
            // TODO: replace this with the user's avatar.
            /*
            const avatar = (
                msg.from === "system" ? "" :
                <i className="material-icons mdl-list__item-avatar">person</i>
            );
            */
            let avatar = '';
            if (this.props.user.avatar && !isReply && msg.from !== 'system') {
                avatar = <img src={this.props.user.avatar} className="avatar" role="presentation" />;
            }
            else if(msg.avatar && msg.from !== 'system') {
                avatar = <img src={msg.avatar} className="avatar" role="presentation" />;
            }

            const chatClasses = (isReply ? 'chatBubble reply' : 'chatBubble') +
                (msg.from === 'system' ? ' notice' : '');

            // Inline links to youtube videos
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
            <form onSubmit={this.onFormSubmit.bind(this)} className="chatForm">
              <div className="mdl-textfield mdl-js-textfield">
                <input className="mdl-textfield__input"
                       type="text"
                       id="message"
                       name="message" />
                <label className="mdl-textfield__label" htmlFor="message">Your Message</label>
              </div>
              <button className="mdl-button mdl-js-button">Send</button>
            </form>
          </div>
        );
    }
}
