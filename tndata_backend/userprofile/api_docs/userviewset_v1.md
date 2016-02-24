This endpoint defines methods that allow you to view, create, and update
User accounts. Additionally, it exposes several bits of user data, therefore
acting as a decently complete single point of information for a User.

Sections in this documentation:

* <a href="#user-data">User Data</a>
* <a href="#creating-a-user">Creating a User</a>
* <a href="#acquiring-an-auth-token">Acquiring an Auth token</a>
* <a href="#logging-out">Logging Out</a>
* <a href="#retrieving-a-users-info">Retrieveing a User's Info</a>
* <a href="#setting-a-password">Setting a Password</a>
* <a href="#options">Options</a>

----

## User Data

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
* `timezone` -- The user's given timezone.
* `date_joined` -- Date the user joined.
* `userprofile_id` -- Unique ID for the [UserProfile](/api/userprofiles/)
* `token` -- The user's [auth token](#acquiring-an-autho-token)
* `needs_onboarding` -- Whether or not the user should go through onboarding.

Collections of related data for the user, include:

* `next_action` -- a `UserAction` object (the mapping between a User and
  an Action`. This is the upcoming activity for the user.
* `action_feedback` is a object of data for the _feedback card_ related to
  the user's `next_action`. It's intention is to _reinforce the user's
  upcoming action with some motivational text_. This content is dynamically
  generated, and will depend on the percentage of completed vs scheduled
  actions for the user. It contains the following data:

    - `title`: Title-text for the motivational message.
    - `subtitle`: A short additional motivational message.
    - `percentage`: percentage of actions completed in some time period.
    - `incomplete`: Number of actions the user did not complete in some
      time period.
    - `completed`: Number of actions completed in some time period.
    - `total`: Number of actions schedule in some time period.
    - `icon`: An integer (1-4) indicating which icon should be used.
      (1: footsteps, 2: thumbs-up, 3: ribbon, 4: trophy (when all are completed))

* `progress` -- an object containing the number of actions completed today,
  the number of total actions scheduled for today, and the percentage of
  those completed.
* `upcoming_actions` -- a list of the `UserAction`s that are relevant for
  today (i.e. the user has a reminder scheduled for today)
* `suggestions` -- a list of suggested `Goal`s for the user.

* `places` -- An array of the [user's Places](/api/users/places/)
* `goals` -- An array of the user's selected [Goals](/api/users/goals/). See the
  [UserGoal documentation](/api/users/goals/) for more info.
* `behaviors` -- An array of the user's selected [Behaviors](/api/users/behaviors/).
  See the [UserBehavior documentation](/api/users/behaviors/)
  for more info.
* `actions` -- An array of the user's selected [Actions](/api/users/actions/)
* `categories` -- An array of the user's [Categories](/api/users/categories/)

## Creating a User <a href="#creating-a-user">&para;</a>

POST to `/api/users/` with the following information:

    {
        "email": "YOUR-EMAIL",
        "password": "YOUR-PASSWORD",
        "first_name": "First",
        "last_name": "Last"
    }

**Note**: `email` and `password` are required! However, `first_name` and
`last_name` are optional.

*Valid Example*:

    {
        "email": "YOUR-EMAIL",
        "password": "YOUR-PASSWORD",
    }


The response includes the created user's info, such as their database id
and the id for their created User Profile *as well as* an Auth Token for
subsequent API requests.

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

## Options <a href="#options">&para;</a>

See the *Options* on this page for more information regarding which fields
are required (during PUT requests).

----

