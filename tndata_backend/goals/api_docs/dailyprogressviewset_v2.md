
**API Version 2**

A user's stats on their daily progress toward selected goals.

<div class="alert alert-info">
    <strong>NOTE:</strong> You can always fetch an authenticated user's
    <a href="#latest-dailyprogress">latest values</a> from the
    <a href="/api/users/progress/latest/"><code>/api/users/progress/latest/</code></a>
    endpoint.
</div>

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
* `engagement_rank`: Where you rank when compared with other user's
  `engagement_15_days` value.
* `engagement_15_days`: 15-day engagement percentage.
* `engagement_30_days`: 30-day engagement percentage.
* `engagement_60_days`: 60-day engagement percentage.
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

## Additional endpoints

There are a few additional API endpoints that you can use to work with
`DailyProgress` data for a user. These include:


### Latest DailyProgress

You can always get the latest values from [/api/users/progress/latest/](/api/users/progress/latest/).

### Daily Check-in

To update a user's daily check-in values for a goal, send a POST request
to `/api/users/progress/checkin/` with the following data:

    {
        'goal': GOAL_ID,
        'daily_checkin': <integer>,
    }

This endpoint will either return a error message when things go wrong, or
will return a serialized version of the `DailyProgress` object.

### Streaks

Retrieve a list of (recent) days in which a user _completed_ an action or
custom action. You can retrieve a user's streaks from `/api/users/progress/streaks/`.

Results will include a list of `["date", int]` values that tells you how many
times the user positively interacted with the app on a particular date (i.e.
self-reported "got it" on some action).

    {
        "count": 30,
        "results": [
            {
                "date": "2016-05-18",
                "day": "Wednesday",
                "count": 4
            },
            {
                "date": "2016-05-19",
                "day": "Thursday",
                "count": 2
            },
            ...
        ]
    }


----

