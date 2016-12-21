import axios from 'axios';
import React, { Component } from 'react';

import Chat from './chat';


// Ensure our chat app hits the api running on the same host
// e.g. ==> ws://127.0.0.1:8000
//
// TODO: now to know if we're using port 8000, or 80, or 443 or what?
let PORT = window.location.port;
if(PORT.length > 0) {
    PORT = ":8000";
}
const ROOT_URL = window.location.hostname + PORT;
const WS_HOST = 'ws://' + ROOT_URL;
const API_HOST = '//' + ROOT_URL;


class App extends Component {

    constructor(props) {
        super(props)
        this.state = {
            userId: '',
            email: '',
            username: '',
            avatar: '',
            firstName: '',
            lastName: ''
        }
        this.fetchUser = this.fetchUser.bind(this);
        this.fetchProfile = this.fetchProfile.bind(this);
    }

    componentWillMount() {
        this.fetchUser();
        this.fetchProfile();
    }

    fetchUser() {
        const url = API_HOST + '/api/users/';
        axios.defaults.headers.common['Authorization'] = 'Token ' + this.props.apiToken;
        axios.get(url).then((resp) => {
            const data = resp.data;
            if(data.count === 1) {
                this.setState({
                    userId: data.results[0].id,
                    email: data.results[0].email,
                    username: data.results[0].username,
                    firstName: data.results[0].first_name,
                    lastName: data.results[0].last_name,
                });
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
        const ws_url = WS_HOST + window.location.pathname;
        return (
          <div>
            <Chat ws_url={ws_url} user={this.state}/>
          </div>
        );
    }
}

export default App;
