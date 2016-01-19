The user's basic account information. When authenticated, a request to
this endpoint should return a result containing one item:


* `id`: The user's unique ID
* `username`: The user's username.
* `email`: Their email address.
* `is_staff`: true or false -- are they a staff user.
* `first_name`: First Name
* `last_name`: Last name
* `timezone`: Their timezone, e.g. `America/Chicago`
* `full_name`: Their full name (first + last concatenated)
* `date_joined`: Date they signed up.
* `userprofile_id`: Unique ID for their `UserProfile` (see the [/api/userprofiles](/api/userprofiles) endpoint.
* `token`: Their auth token for the app.
* `needs_onboarding`: true or false -- should they go through onboarding.

----
