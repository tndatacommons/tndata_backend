tndata userprofile
==================

This is the `userprofile` app for te TN Data Commons backend system. It provides
a user profile model as well as additional utilities regarding user accounts.


Authorization/Authentication
----------------------------

This app contains the API endpoints used for user creation, authentication,
and authorization.


Usage
-----

**Creating a User**: POST to `/api/users/` with the following info:

    {"username": "YOUR-USERNAME",
     "password": "YOUR-PASSWORD",
     "email": "YOUR-EMAIL",
     "first_name": "First",
     "last_name": "Last",}

The response includes the created user's info, such as their database id and
the id for their created User Profile *as well as* an Auth Token for subsequent
API requests.

**Acquiring an Auth token**. POST to `/api/auth/token/` with a `username` and
`password`. The response will contain a `token` attribute, which you can then
include with subsequent requests. Include the token in an `Authorization` HTTP
header, where the token is prefixed by the string, "Token", e.g.:

    Authorization: Token <token-value-here>

You can use curl to test authenticated reqeusts, e.g.:

    curl -X GET http://app.tndata.org/api/users/ -H 'Authorization: Token <YOUR-TOKEN>'

**Setting a Password**. Send a PUT request to `/api/users/{id}/` incuding at
least `{'username': <their username>, 'password': <new password>}`

**Retrieving a User's Info**: Send a GET request to `/api/users/` or to `/api/users/{id}/`.
This should include a single result set that contains the authenticated user.
