The user's basic account information. This is a combination of `User` and
`UserProfile`. When authenticated, a request to this endpoint should return a
result containing one item:


* `id`: The user's unique ID
* `username`: The user's username.
* `email`: Their email address.
* `is_staff`: true or false -- are they a staff user.
* `first_name`: First Name
* `last_name`: Last name
* `full_name`: Their full name (first + last concatenated)
* `timezone`: Their timezone, e.g. `America/Chicago`
* `date_joined`: Date they signed up.
* `userprofile_id`: Unique ID for their `UserProfile` (see the [/api/userprofiles](/api/userprofiles) endpoint.
* `token`: Their auth token for the app.
* `needs_onboarding`: true or false -- should they go through onboarding.
* `maximum_daily_notifications`:  Number of daily notifications the user should receive
* `zipcode`:  The user's home zipcode.
* `birthday`:  The user's birthday, e.g. 1990-12-25 (for Dec 25, 1990)
* `sex`:  A string, "female" or "male
* `employed`:  Boolean: `true` if employed.
* `is_parent`: Boolean: `true` if the user is a parent.
* `in_relationship`:Boolean: `true` if the user is in a relationship.
* `has_degree`:Boolean: `true` if the user has a degree.
* `object_type`:  A string, should always be 'user'

----
