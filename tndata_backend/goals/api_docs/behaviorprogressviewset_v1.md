This endpoint allows a user to record their daily 'self-assessed'
progress toward a Behavior, and retrieve a history of that progress.

This model also contains daily aggregates of completed actions that are
children of the behavior.

GET requests will return the following information for an authenticated user:

* `id`: Unique ID for a `BehaviorProgress` object.
* `user`: ID of the authenticated user.
* `user_behavior`: ID of the associated `UserBehavior` (User-to-Behavior mapping)
* `status`: Value of their progress, in the range of 1-3
* `status_display`: Human-readable status of the user's progress.
* `daily_actions_total`: The total number of actions contained within the
  Behavior that were scheduled for the day.
* `daily_actions_complete`:  The number of actions within the Behavior that
  were completed during the day.
* `daily_action_progress`: The percentage of actions completed. Calculated
  vial `daily_actions_completed` / `daily_actions_total`.
* `daily_action_progress_percent`: The same as `daily_action_progress`, but
  as an integer percent instead of a decimal.
* `reported_on`: Date on which progress was initially reported.

## Saving Progress

To record progress toward a behavior, send a POST request containing the
following information:

* `status`: A numerical value, 1 for "Off Course", 2 for "Seeking", and 3
  for "On Course".
* `behavior`: The ID for the Behavior. Optional if `user_behavior` is provided
* `user_behavior`: The ID for the `UserBehavior` instance (the mapping
  between a User and a Behavior). Optional if `behavior` is provided.

This will create a new BehaviorProgress snapshot. _However_, if an instance
of a BehaviorProgress alread exists for the day in which this data is POSTed,
that instance will be updated (so that there _should_ only be one of these
per day).

## Updating Progress

You may also send a PUT request to `/api/users/behaviors/progress/{id}/`
with the following information to update an existing `BehaviorProgress`
instance:

* `status`: A numerical value, 1 for "Off Course", 2 for "Seeking", and 3
  for "On Course".
* `user_behavior`: The ID for the `UserBehavior` instance (the mapping
  between a User and a Behavior).

----

