
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


### Removal

Users may be removed from an Organization by POSTing to the organization's
_remove member_ endpoint:  `/api/organizations/{Organization ID}/remove-member/`

**NOTE** removing a member from an organization is a destructive operation,
and will also remove the following data associated with the Organization:

- Programs in which the user is enrolled
- The user's selected categories
- The user's selected goals
- The user's selected actions

----
