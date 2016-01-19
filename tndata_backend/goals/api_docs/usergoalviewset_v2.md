This endpoint represents a user's selected goals. That is, it's an object
that defines a mapping between [Users](/api/users/) and
[Goals](/api/goals/).

GET requests to this page will simply list this mapping for the authenticated
user.

## Fields

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserGoal` mapping.
* `user`: The Unique identifier for the `User`
* `goal`: An object that represents the `Goal` selected by the user
* `primary_category`: The ID of the primary category for this goal
* `created_on`: Time at which the user selected this item.
* `editable`: A boolean that indicates whether or not a user
  should be able to customize the reminders beneath this content

## Adding a Goal

To associate a Goal with a User, POST to `/api/users/goals/` with the
following data:

    {'goal': GOAL_ID}

## Viewing the Goal data

Additional information for the Goal mapping is available at
`/api/users/goals/{usergoal_id}/`. In this case, `{usergoal_id}` is the
database id for the mapping between a user and a goal.

## Removing a Goal from the user's list.

Send a DELETE request to the usergoal mapping endpoint:
`/api/users/goals/{usergoal_id}/`.

## Update a Goal Mapping.

Updating a goal mapping is currently not supported.

## Additional information

The Goals that a User has selected are also available through the
`/api/users/` endpoint as a `goals` object on the user.

----

