
**API Version 2**

A user's stats on their daily progress toward selected goals.

## Fields

This endpoint returns resources with the following fields.


* `id`: A unique identifier for the `DailyProgress` object.
* `user`: A unique identifier for the `User`
* `actions_total`: The total number of actions selected by the user for all time.
* `actions_completed`: Number actions marked completed for the day
* `actions_snoozed`: Number of actions snoozed for the day
* `actions_dismissed`:  Number of actions dismissed for the day
* `customactions_total`: Total number of custom actions created (for all time)
* `customactions_completed`: Number custom actions marked completed for the day
* `customactions_snoozed`: Number of custom actions snoozed for the day
* `customactions_dismissed`:  Number of custom actions dismissed for the day
* `behaviors_total`: Total number of `Behavior`s selected by the user for all time.
* `behaviors_status`: A JSON object that describes the user's status for
  notifications received that are related to each selected Behavior.
* `goal_status`: A JSON object that lists the user's daily check-in status
  for selected goals.
* `updated_on`: Date progress was last updated.
* `created_on`: Date this instance was created.
* `object_type`: Will always be 'dailyprogress'

## Progress Details

Individual daily progress details are available at `/api/users/progress/{id}/`.

## Update progress

Send a PUT request with values you wish to update to the detail url:
`/api/users/progress/{id}/`. For example, the following would change the
number of actions completed: `{'actions_completed': 5}`

## Daily Check-in

To update a user's daily check-in values for a goal, send a POST request
to `/api/users/progress/checkin/` with the following data:

    {
        'goal': GOAL_ID,
        'daily_checkin': <integer>,
    }

This endpoint will either return a error message when things go wrong, or
will return a serialized version of the `DailyProgress` object.

----

