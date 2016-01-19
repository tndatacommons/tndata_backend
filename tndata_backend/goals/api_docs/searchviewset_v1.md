This endpoint represents a mapping between [Users](/api/users/) and
[Behaviors](/api/behaviors/).

GET requests to this page will simply list this mapping for the authenticated
user.

## Fields

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserBehavior` mapping.
* `user`: A unique identifier for the `User`
* `behavior`: An object that represents the `Behavior` selected by the user
* `behavior_progress`: An object containing information on the user's
  progress toward the completion of their scheduled actions within this
  behavior. It contains the following information:

    - `id`: a unique id for the GoalProgress instance.
    - `user`: the user's unique id
    - `user_behavior`: The unique id of the parent UserBehavior
    - `status`: An integer representing the user's daily reported progress,
      (1 means Off Course, 2 is Seeking, 3 is On Course).
    - `status_display`: A human-readable version of status.
    - `daily_actions_total`: Number of actions scheduled for _this day_.
    - `daily_actions_completed`: Number of actions the user completed in
      _this day_
    - `daily_action_progress`: Daily progress percentage (as a float). This
      is calculated with `daily_actions_completed` / `daily_actions_total`
    - `reported_on`: Date/Time on which this data was recorded.
    - `object_type`: Will always be `behaviorprogress`

* `custom_trigger`: (will be `null`). This is currently not implemented.
* `custom_triggers_allowed`: A boolean that indicates whether or not a user
  should be able to customize the reminders beneath this content
* `user_categories`: An array of `Category` objects that have been selected
  by the user, and that are also parents of this behavior (through Goals)
* `user_goals`: An array of `Goal` objects that have been selected by the
  user, and that are also parents of this behavior.
* `user_actions_count`: the number of child Actions that the user has
  selected that are contained in this behavior.
* `user_actions`: An array of `Action` objects selected by the user.
* `created_on`: Time at which the user selected this item.

## Adding a Behavior

To associate a Behavior with a User, POST to `/api/users/behaviors/` with the
following data:

    {'behavior': BEHAVIOR_ID}

## Adding multiple Behaviors in one request

This endpoint also allows you to associate multiple behaviors with a user
in a single request. To do this, POST an array of behavior IDs, e.g.:

    [
        {'behavior': 3},
        {'behavior': 4},
        {'behavior': 5}
    ]

## Removing multiple Behaviors in one request.

This endpoint also allows you to remove  multiple instances of the
user-to-behavior association. Tod do this, send a DELETE request with
an array of `userbehavior` IDs, e.g.:

    [
        {'userbehavior': 3},
        {'userbehavior': 4},
        {'userbehavior': 5}
    ]

## Viewing the Behavior data

Additional information for the Behavior mapping is available at
`/api/users/behaviors/{userbehavior_id}/`. In this case, `{userbehavior_id}`
is the database id for the mapping between a user and a behavior.

## Removing a Behavior from the user's list.

Send a DELETE request to the userbehavior mapping endpoint:
`/api/users/behaviors/{userbehavior_id}/`.

## Update a Behavior Mapping.

Updating a behavior mapping is currently not supported.

## Update a Behavior Mapping / Custom Triggers

Behavior Mappings may be updated in order to set custom Triggers (aka
reminders) for the associated behavior.

To do this, send a PUT request to the detail url
(`api/users/behaviors/{userbehavior_id}`) with the following information:

* `custom_trigger_time`: The time at which the reminder should fire, in
  `hh:mm` format.
* `custom_trigger_rrule`: A Unicode RFC 2445 string representing the days &
  frequencies at which the reminder should occur.

## Filtering

UserBehaviors can be filtered using a querystring parameter. Currently,
filtering is availble for Goals. You can filter by an ID or a slug.

To retrieve all *UserBehavior*s that belong to a particular goal, use
one of the following:

* `/api/behaviors/?goal={goal_id}` or by slug
* `/api/behaviors/?goal={goal_title_slug}`

## Additional information

The Behaviors that a User has selected are also available through the
`/api/users/` endpoint as a `behaviors` object on the user.

Each results object also includes a `user_goals` object in addition to
a `behavior` object. The `user_goals` object is a list of Goals in
which the behavior belongs that have also be selected by the User. Related:
[/api/users/goals/](/api/users/goals/).

----

