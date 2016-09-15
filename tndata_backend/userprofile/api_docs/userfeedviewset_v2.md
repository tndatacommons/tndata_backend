
The User Feed of information: home-feed data for the user, include:

* `progress` -- an object containing the number of actions completed today,
  the number of total actions scheduled for today, and the percentage of
  those completed.

    - `total`: Total number of actions scheduled for today
    - `completed`: Total number of actions completed today
    - `progress`: A progress score (currently unused)
    - `engagement_rank`: How the user ranks with their peers using the app.
    - `weekly_completions`: The number of tips the user has completed in the
      last 7 days.

* `suggestions` -- (currently disabled)
* `upcoming` -- an array of upcoming UserAction or CustomAction objects. This
  array contains objects with the following bits of data:

    - `action_id`: ID for the UserAction or CustomAction object.
    - `action`: Title for the UserAction/Customaction
    - `goal_id`: ID for the primary Goal or CustomGoal
    - `goal`: Title for the primary Goal or CustomGoal
    - `category_color`: A hex string for the color
    - `category_id`: ID for the primary Category, -1 for custom actions
    - `trigger`: date/time for the next trigger
    - `type`: will be `useraction` or `customaction`
    - `object_type`: will always be "`upcoming_item`"

* `funcontent` -- An object representing _reward_ content. See also
   the [/api/rewards/](/api/rewards/) endpoint. Will contain:

    - `id`: ID for the reward content.
    - `message`: Message for the reward content.
    - `author`: (possibly empty). If the message has a author, they'll be
      listed here.
    - `message_type`: One of the following: `quote`|`fortune`|`fact`|`joke`
    - `object_type`: A string that will always be "funcontent"

* `object_type` -- a string. Will always be "feed"

----
