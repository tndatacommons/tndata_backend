import axios from 'axios';
import React, { Component } from 'react';

import Chat from './chat';

// If we're running over http, use ws://, if over https, use wss://
const PROTOCOLS = {
    'https:': 'wss://',
    'http:': 'ws://',
}

// Ensure our chat app hits the api running on the same host
// e.g. ==> ws://127.0.0.1:8000
//
// TODO: now to know if we're using port 8000, or 80, or 443 or what?
let PORT = window.location.port;
if(PORT.length > 0) {
    PORT = ":8000";
}
const ROOT_URL = window.location.hostname + PORT;
const WS_HOST = PROTOCOLS[window.location.protocol] + ROOT_URL;

const API_HOST = '//' + ROOT_URL;


class App extends Component {

    constructor(props) {
        super(props)
        this.state = {
            user: {
                userId: '',
                email: '',
                username: 'Unknown',
                avatar: '',
                firstName: 'Unkown',
                lastName: 'User'
            },
            chatHistory: []
        }
        this.fetchMessageHistory = this.fetchMessageHistory.bind(this);
        this.fetchUser = this.fetchUser.bind(this);
        this.fetchProfile = this.fetchProfile.bind(this);
    }

    componentWillMount() {
        this.fetchUser();
        this.fetchProfile();
    }

    fetchMessageHistory(currentUserId) {
        // NOTE: Called *after* we know the user's details, which we need
        // in order to construct the room name.
        const toUser = window.location.pathname.replace('/chat/', '').replace('/', '');
        const room = [currentUserId, toUser].sort().join("-");
        const url = API_HOST + '/api/chat/history/?room=chat-' + room;

        axios.defaults.headers.common['Authorization'] = 'Token ' + this.props.apiToken;
        axios.get(url).then((resp) => {
            const data = resp.data;
            if(data.count > 0) {
                this.setState({user: this.state.user, chatHistory: data.results});
            }
        });

    }
    fetchUser() {
        const url = API_HOST + '/api/users/';
        axios.defaults.headers.common['Authorization'] = 'Token ' + this.props.apiToken;
        axios.get(url).then((resp) => {
            const data = resp.data;
            if(data.count === 1) {
                const userData = {
                    userId: data.results[0].id,
                    email: data.results[0].email,
                    username: data.results[0].username,
                    firstName: data.results[0].first_name,
                    lastName: data.results[0].last_name,
                }
                this.setState({user: userData, chatHistory: this.state.chatHistory});
                this.fetchMessageHistory(data.results[0].id);
            }
        });

    }

    fetchProfile() {
        const url = API_HOST + '/api/users/profile/';
        axios.defaults.headers.common['Authorization'] = 'Token ' + this.props.apiToken;
        axios.get(url).then((resp) => {
            const data = resp.data;
            if(data.count === 1) {
                this.setState({
                    avatar: data.results[0].google_image
                });
            }
        });
    }

    render() {
        const path = window.location.pathname;
        const ws_url = WS_HOST + path;
        return (
          <div>
            <Chat
                ws_url={ws_url}
                user={this.state.user}
                history={this.state.chatHistory} />
          </div>
        );
    }
}

export default App;
