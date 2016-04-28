
**API Version 2**

This endpoint represents a user's selected Behaviors. That is, it's an object
that defines a mapping between [Users](/api/users/) and
[Behaviors](/api/behaviors/).

GET requests to this page will simply list `UserBehavior` objects belonging to
the authenticated user.

## Fields

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserBehavior` mapping.
* `user`: A unique identifier for the `User`
* `behavior`: An object that represents the `Behavior` selected by the user
* `editable`: A boolean that indicates whether or not a user
  should be able to customize the reminders beneath this content
* `created_on`: Time at which the user selected this item.

## Adding a UserBehavior

To associate a Behavior with a User, POST to `/api/users/behaviors/` with the
following data:

    {'behavior': BEHAVIOR_ID}

## Adding a UserBehavior and all parent objects at once

If you submit a `category`, `goal`, and `behavior`, all in a single payload,
each object will be added to the user's collection at once; This will simplify
adding the tree of data. When using this payload, all items are required.

    {
        'behavior': BEHAVIOR_ID,
        'goal': GOAL_ID,
        'category': CATEGORY_ID
    }

## Viewing the UserBehavior data

Additional information for the Behavior mapping is available at
`/api/users/behaviors/{userbehavior_id}/`. In this case, `{userbehavior_id}`
is the database id for the mapping between a user and a behavior.

## Deleting a UserBehavior

Send a DELETE request to the userbehavior mapping endpoint:
`/api/users/behaviors/{userbehavior_id}/`.

## Update a UserBehavior

Updating a behavior mapping is currently not supported.

## Filtering

UserBehaviors can be filtered using a querystring parameter. Currently,
filtering is availble for Goals. You can filter by an ID or a slug.

To retrieve all UserBehaviors that belong to a particular goal, use
one of the following:

* `/api/behaviors/?goal={goal_id}` or by slug
* `/api/behaviors/?goal={goal_title_slug}`

----
