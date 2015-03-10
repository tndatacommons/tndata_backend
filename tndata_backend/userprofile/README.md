tndata userprofile
==================

This is the `userprofile` app for te TN Data Commons backend system. It provides
a user profile model as well as additional utilities regarding user accounts.


Authorization/Authentication
----------------------------

This app contains the API endpoints used for user creation, authentication,
and authorization.


Views
-----

TODO: explain how to do authn/authz.

* **Acquiring an Auth token**. For existing users, send an POST request to
 `/api/auth/token/` including a `username` and `password`. The response will
 contain a `token` attribute.

* All other views in this app required that token in order to retrieve relevant
 information. Include the token in an Authorization HTTP header, where the token
 is prefixed by the string, "Token", e.g.:

    Authorization: Token <token-value-here>

* Note: You can use curl to test the above:

    curl -X GET http://example.com/api/users/ -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'

