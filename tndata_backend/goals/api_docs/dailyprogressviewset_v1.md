
A user's stats on their daily progress toward selected goals.

## Fields

This endpoint returns resources with the following fields.


* `id`: A unique identifier for the `DailyProgress` object.
* `user`: A unique identifier for the `User`
* `actions_total`: Total number of actions selected
* `actions_completed`: Number actions marked completed for the day
* `actions_snoozed`: Number of actions snoozed for the day
* `actions_dismissed`:  Number of actions dismissed for the day
* `updated_on`: Date progress was last updated.
* `created_on`: Date this instance was created.
* `object_type`: Will always be 'dailyprogress'

## Progress Details

Individual daily progress details are available at `/api/users/progress/{id}/`.

## Update progress

Send a PUT request with values you wish to update to the detail url:
`/api/users/progress/{id}/`. For example, the following would change the
number of actions completed: `{'actions_completed': 5}`


----

