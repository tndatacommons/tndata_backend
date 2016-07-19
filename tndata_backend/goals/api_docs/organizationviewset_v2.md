
**API Version 2**

Users may be members of one or more Organizations, and these organizations may
have specific categories and goals associated with them.

Each Organization has at least the following fields:

* `id`: The unique database identifier for the category
* `name`: The name of the organization.
* `name_slug`: The unique slug.

## Membership

Users may be _members_ of an organization. To retrive a user's organization
membership, send a GET request to [/api/organizations/members/](/api/organizations/members).

To add a user to a new organization, send a POST request to
`/api/organizations/members` with the following payload:

    {'organization': <organization_id>}


----
