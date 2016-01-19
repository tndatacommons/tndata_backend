This endpoint represents a user's selected categories. That is, it's an
object that defines a mapping between [Users](/api/users/) and
[Categories](/api/categories/).

GET requests to this page will simply list this mapping for the authenticated
user.

## Fields

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserCategory` mapping.
* `user`: A unique identifier for the `User`
* `category`: An object that represents the `Category` selected by the user
* `created_on`: Time at which the user selected the Category.
* `editable`: A boolean that defines whether or not the user should be able to
  edit triggers within the category. (formerly: `custom_triggers_allowed`)
* `object_type`: Will always be the string `usercategory`

## Adding a Category

To associate a Category with a User, POST to `/api/users/categories/` with the
following data:

    {'category': CATEGORY_ID}

## Adding multiple Categories in one request

This endpoint also allows you to associate multiple categories with a user
in a single request. To do this, POST an array of category IDs, e.g.:

    [
        {'category': 3},
        {'category': 4},
        {'category': 5}
    ]

## Removing multiple Categories in one request.

This endpoint also allows you to remove  multiple instances of the
user-to-category association. Tod do this, send a DELETE request with
an array of `usercategory` IDs, e.g.:

    [
        {'usercategory': 3},
        {'usercategory': 4},
        {'usercategory': 5}
    ]

## Viewing the Category data

Additional information for the Category mapping is available at
`/api/users/categories/{usercategory_id}/`. In this case, `{usercategory_id}`
is the database id for the mapping between a user and a category

## Removing a Category from the user's list.

Send a DELETE request to the usercategory mapping endpoint:
`/api/users/categories/{usercategory_id}/`.

## Update a Category Mapping.

Updating a category mapping is currently not supported.

## Additional information

The Categories that a User has selected are also available through the
`/api/users/` endpoint as a `categories` object on the user.

Each results object also includes a `user_goals` object in addition to
a `category` object. The `user_goals` object is a list of Goals that are
contained in the Category, and have also be selected by the User. Related:
[/api/users/goals/](/api/users/goals/).

----

