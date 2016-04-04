This endpoint defines a simpler, more efficient view into the User's _Profile_.
User Profiles are created automatically after a user account is created, so
this endpoint does not support creation (i.e. POST requests).

## Fields

- `id`: The unique database ID for the UserProfile object.
- `user`:  The ID for the user that owns the profile.
- `timezone`: The user's timezone, as a string, e.g. "America/Chicago"
- `maximum_daily_notifications`: The user's preferred number of daily notifications.
- `needs_onboarding`: Boolean: Whether or not the user needs to go through onboarding.
- `zipcode`: The user's zip code (US-only)
- `birthday`: The user's birthday, formatted as YYYY-MM-DD
- `sex`: The user's sex, can be "male", "female", or omitted.
- `employed`: Boolean: Whether or not the user is employed
- `is_parent`: Boolean: Whether or not the user is a parent
- `in_relationship`: Boolean: Whether or not the user is in a relationship
- `has_degree`: Boolean: Whether or not the user has a college degree
- `updated_on`: Date this record was last updated.
- `created_on`: Date this record was created.
- `object_type`: The type of object; this is always "profile"


## Updating

Currently all of the above fields are optional. To update a user's profile,
send a PUT request containing the relevant new information to the detail
endpoint: `/api/users/profile/{d}/`, for example:

    {'timezone': 'America/Chicago', 'needs_onboarding': false}

## Retrieving a User Profile

Send a GET request to `/api/users/profile/` or to
`/api/users/profile/{id}/`. A User's profile id is also available as
part of their [user data](/api/users/).

----

