This defines methods for viewing and updating a User's _Profile_. User
Profiles are created automatically after a user account is created.

## Updating

Currently the only portion of a UserProfile that can be updated is their
`timezone` and the `needs_onboarding` fields. To set a user's timezone,
send a PUT request to the UserProfile's detail endpoint,
`/api/userprofiles/{userprofile_id}/`, including the string for the
desired timezone.

    {'timezone': 'America/Chicago'}

Or to update both fields:

    {'timezone': 'America/Chicago', 'needs_onboarding': false}

## Retrieving a User Profile

Send a GET request to `/api/userprofiles/` or to
`/api/userprofiles/{profile-id}/`. A User's profile id is available as
part of their [user data](/api/users/). This should include a single
result set that contains the authenticated user.

## Bio Information

The `bio` attribute contains the questions and the authenticated user's
answers (if any) to the
[Bio survey](http://app.tndata.org/api/survey/instruments/4/).

----

