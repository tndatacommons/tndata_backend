This endpoint allows a user to record and/or update their daily check-in
progress toward a Goal, and retrieve a history of that progress.

Each item in this result contains a number of fields. The basic ones are:

* `id`: The object's unique ID.
* `goal`: The ID of the related Goal.
* `usergoal`: The ID of the `UserGoal` (user-to-goal mapping)
* `reported_on`: The date/time on which this object was initially created.

The following fields were used in a (now deprecated) daily 3-scale behavior
check-in:

* `current_score`: aggregate value for the user's behaviors in this goal.
* `current_total`: sum of user's check-in values.
* `max_total`: maximum possible value

The following are the new daily check-in values:

* `daily_checkin`: The user's daily check-in value for this goal.
* `weekly_checkin`: Average over the past 7 days.
* `monthly_checkin`: Average over the past 30 days.

The following are stats calculated based on actions that the user has
completed. The weekly values are average over 7 days while the rest (e.g.
`action_progress`) are averaged over 30 days:

* `daily_actions_total`: The total number of Actions the user had scheduled
  within this goal.
* `daily_actions_completed`: The number of actions completed.
* `daily_action_progress`: Percentage of completed vs. incomplete (as a decimal)
* `daily_action_progress_percent`: Percentage of completed vs. incomplete
  (as an integer)
* `weekly_actions_total`
* `weekly_actions_completed`
* `weekly_action_progress`
* `weekly_action_progress_percent`
* `actions_total`
* `actions_completed`
* `action_progress`
* `action_progress_percent`

## Saving Progress

To record progress toward a goal, send a POST request containing the
following information:

* `goal`: The ID for the Goal.
* `daily_checkin`: An integer value in the range 1-5 (inclusive)

This will create a new GoalProgress snapshot. _However_, if an instance
of a GoalProgress alread exists for the day in which this data is POSTed,
that instance will be updated (so that there _should_ only be one of these
per day).

## Updating Progress

You may also update a GoalProgress by sending a PUT request to
`/api/users/goals/progress/{id}/` containing the same information that
you'd use to create a Goalprogress.

## Getting Average Progress

You may set a GET request to the
[/api/users/goals/progress/average/](/api/users/goals/progress/average/]
endpoint to retrive an average daily and weekly progress. These values
are averaged over the past 7 days, and are compared with a given `current`
value.

For example, if the user's current goal progress feed back average is `5`,
send the following GET request:

    /api/users/goals/progress/average/?current=5

The full result of this endpoint contains the following information:

* `daily_checkin_avg` - Average of _all_ GoalProgress.daily_checkin
  values for the user for _today_.
* `weekly_checkin_avg` - Average GoalProgress.daily_checkin values over
  the past 7 days.
* `better`: True if current is > daily_checkin_avg, False otherwise.
* `text`: Some display text based on the value of `better`.

----

