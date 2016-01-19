This endpoint allows a user retreive and update their enrollment
information for "packaged content".

GET requests will return the following information for an authenticated
user:

* `user`: ID of the authenticated user.
* `accepted`: Whether or not the user has accepted the enrollment.
* `updated_on`: Date at which this enrollment was last updated.
* `enrolled_on`: Date on which the user was enrolled.
* `category`: the category / package in which the user is enrolled. This
  representation of a category is slightly different from others in the API,
  because it includes both markdown and html versions of consent fields:
  `consent_summary`, `html_consent_summary`, `consent_more`, and
  `html_consent_more`.
* `goals`: an array of goals that are included in this category / package

## Accepting the Enrollment

When users are enrolled into packaged content, they must indeicate their
acceptance of the _consent_ (`consent_summary`, `consent_more`). To
update a user's acceptance, send a PUT request to the detail endpoint
for a PackentEnrollment.

PUT to `/api/users/packages/{id}/` with:

    {'accepted': True}

This will indicate they've accepted the terms of the enrollment, and the
packaged content will be available with the rest of the content.

----

