
**API Version 2**

Users may be members of one or more Programs, and these programs may
have specific categories and goals associated with them.

Each Program has at least the following fields:

* `id`: The unique database identifier for the Program
* `name`: The name of the program.
* `name_slug`: The unique slug.
* `organization`: The name of the organization to which the Program belongs

## Membership

Users may be _members_ of a program. To retrive a user's program
membership, send a GET request to [/api/programs/members/](/api/programs/members).

To add a user to a new program, send a POST request to
`/api/programs/members` with the following payload:

    {'program': <program_id>}

Adding a user as a member to a program will also make them a member of the
Program's organization (see [/api/organizations/members/](/api/organizations/members/)).

----
