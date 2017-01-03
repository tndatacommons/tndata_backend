This endpoint defines methods that allow you to view, create, and update
User accounts.

Sections in this documentation:

* <a href="#fields">Fields</a>
* <a href="#creating-a-user">Creating a User</a>
* <a href="#creating-a-user-via-oauth-google-login">Creating a User via OAuth (Google Login)</a>
* <a href="#acquiring-an-auth-token">Acquiring an Auth token</a>
* <a href="#logging-out">Logging Out</a>
* <a href="#retrieving-a-users-info">Retrieveing a User's Info</a>
* <a href="#setting-a-password">Setting a Password</a>

----

## Fields <a href="#fields">&para;</a>

The following user data is available from this endpoint as an item in the
`results` array.

* `id` -- Unique database ID for the User.
* `username` -- The user's username. For users that sign up through the app,
  the is a unique hash and is not human-friendly.
* `email` -- the user's email address.
* `is_staff` -- True or False: Indicates if users can log in to admin tools.
* `first_name` -- The user's first name.
* `last_name` -- The user's last name.
* `full_name` -- Combination of first and last name
* `date_joined` -- Date the user joined.
* `userprofile_id` -- Unique ID for the [UserProfile](/api/userprofiles/)
* `token` -- The user's [auth token](#acquiring-an-autho-token)
* `object_type` -- A string that will always be 'user'

## Creating a User <a href="#creating-a-user">&para;</a>

POST to `/api/users/` with the following information:

    {
        "email": "YOUR-EMAIL",
        "password": "YOUR-PASSWORD",
        "first_name": "First",
        "last_name": "Last"
    }

**Note**: A combination of (`email` and `password`) or
(`username` and `password`) are required! However, `first_name` and `last_name`
are optional.

*Valid Example*:

    {
        "email": "YOUR-EMAIL",
        "password": "YOUR-PASSWORD",
    }


The response includes the created user's info, such as their database id
and the id for their created User Profile *as well as* an Auth Token for
subsequent API requests.

## Creating a User via OAuth (Google Login) <a href="#creating-a-user-via-oauth-google-login">&para;</a>

Given an OAuth response (e.g. from Google login), send a POST request to
`/api/users/oauth/` with the following payload:

    {
        "email": "YOUR-EMAIL",
        "first_name": "FIRST NAME",
        "last_name": "LAST NAME",
        "image_url": "http://.../photo.jpg",
        "oauth_token": "GOOGLE-AUTH-TOKEN-HERE",
    }

The response from this endpoint will include the User's account and a subset
of profile data (including an auth Token for this API).

**NOTE: When creating an account using this method, the user will not have a
password (though they can go through the password reset process to get one).**

Successful requests to this endpoint will return the following data:

    {
        "id": 123,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@gmail.com",
        "google_image": "https://lh5.googleusercontent.com/.../photo.jpg",
        "google_token": "123456789012345678901",
        "token": "1234567890123456789012345678901234567890",
    }

In the above, `token` is the user's API token for interacting with _this_ API,
while the `google_token` is the verified token to interact with any Google APIs.

## Acquiring an Auth token <a href="#acquiring-an-auth-token">&para;</a>

POST to `/api/auth/token/` with either an  email/password pair:

    {"email": "YOUR-EMAIL", "password": "YOUR-PASSWORD"}


The response will contain a `token` attribute, which you can then include
with subsequent requests. Include the token in an `Authorization` HTTP
header, where the token is prefixed by the string, "Token", e.g.:

    Authorization: Token <token-value-here>

You can use curl to test authenticated reqeusts, e.g.:

    curl -X GET http://app.tndata.org/api/users/ -H 'Authorization: Token <YOUR-TOKEN>'

## Logging out <a href="#logging-out">&para;</a>

A client of the api can log out of the api by sending a POST request to
`/api/auth/logout/`. Include additional details in that request to trigger
side effects (e.g. POST a `{registration_id: 'YOUR-REGISTRATION-ID'}` payload
to remove your device's GCM registration on logout.

## Retrieving a User's Info <a href="#retrieving-a-users-info">&para;</a>

Send a GET request to `/api/users/` or to `/api/users/{id}/`.
This should include a single result set that contains the authenticated user.

## Setting a Password <a href="#setting-a-password">&para;</a>

Send a PUT request to `/api/users/{id}/` including at least the following:

    {'username': <their username>, 'password': <new password>}


----

