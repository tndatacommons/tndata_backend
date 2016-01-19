This endpoint represents a mapping between [Users](/api/users/) and
[Goals](/api/goals/).

GET requests to this page will simply list this mapping for the authenticated
user.

## Fields

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserGoal` mapping.
* `user`: A unique identifier for the `User`
* `goal`: An object that represents the `Goal` selected by the user
* `user_categories`: An array of `Category` objects selected by the user,
  that are also parents of this goal.
* `primary_category`: The primary category for this goal, based on the
  user's selection.
* `user_behaviors_count`: the number of child Behaviors that the user has
  selected that are contained in this goal.
* `user_behaviors`: An array of `Behavior` objects selected by the user.
* `created_on`: Time at which the user selected this item.
* `progress_value`: The user's self-reported progress toward *Behaviors* in
  this goal.
* `goal_progress`: An object containing information on the user's progress
  toward the completion of their scheduled actions within this goal. It
  contains the following information:

    - `id`: a unique id for the GoalProgress instance.
    - `goal`: the goal's unique id
    - `usergoal`: The unique id of the parent UserGoal
    - `current_score`: The aggregate Behavior-rerporting score.
    - `current_total`: The sum of user-reported behavior progresses within
      this goal.
    - `max_total`: The maximum possible value for the Behavior-reported score.
    - `daily_actions_total`: Number of actions scheduled for _this day_.
    - `daily_actions_completed`: Number of actions the user completed in
      _this day_
    - `daily_action_progress`: Daily progress percentage (as a float). This
      is calculated with `daily_actions_completed` / `daily_actions_total`
    - `daily_action_progress_percent`: The daily progress expressed as an
      integer percentage.
    - `weekly_actions_total`: Number of actions scheduled for the past 7 days
    - `weekly_actions_completed`: Number of actions completed over the past
      7 days
    - `weekly_action_progress`: Percentage of completed actions for the week.
    - `weekly_action_progress_percent`: The weekly progress expressed as an
      integer percentage.
    - `actions_total`:  Number of actions scheduled for our historical
      reporting period
    - `actions_completed`: Number of actions completed during our historical
      reporting period.
    - `action_progress`:  Percentage of actions completed (as a float) during
      the historical reporting period.
    - `action_progress_percent`: The progress expressed as an integer
      percentage.
    - `reported_on`: Date/Time on which this data was recorded.

* `custom_triggers_allowed`: A boolean that indicates whether or not a user
  should be able to customize the reminders beneath this content

## Adding a Goal

To associate a Goal with a User, POST to `/api/users/goals/` with the
following data:

    {'goal': GOAL_ID}

## Adding multiple Goals in one request

This endpoint also allows you to associate multiple goals with a user
in a single request. To do this, POST an array of goal IDs, e.g.:

    [
        {'goal': 3},
        {'goal': 4},
        {'goal': 5}
    ]

## Removing multiple Goals in one request.

This endpoint also allows you to remove  multiple instances of the
user-to-goal association. Tod do this, send a DELETE request with
an array of `usergoal` IDs, e.g.:

    [
        {'usergoal': 3},
        {'usergoal': 4},
        {'usergoal': 5}
    ]

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

Each results object also includes a `user_categories` object in addition to
a `goal` object. The `user_categories` object is a list of Categories in
which the goal belongs that have also been selected by the User. Related:
[/api/users/categories/](/api/users/categories/).

----

