
The User Feed of information: home-feed data for the user, include:

* `action_feedback` is a object of data for the _feedback card_ related to
  the user's `next_action`. It's intention is to _reinforce the user's
  upcoming action with some motivational text_. This content is dynamically
  generated, and will depend on the percentage of completed vs scheduled
  actions for the user. It contains the following data:

    - `title`: Title-text for the motivational message.
    - `subtitle`: A short additional motivational message.
    - `percentage`: percentage of actions completed in some time period.
    - `incomplete`: Number of actions the user did not complete in some
      time period.
    - `completed`: Number of actions completed in some time period.
    - `total`: Number of actions schedule in some time period.
    - `icon`: An integer (1-4) indicating which icon should be used.
      (1: footsteps, 2: thumbs-up, 3: ribbon, 4: trophy (when all are completed))

* `progress` -- an object containing the number of actions completed today,
  the number of total actions scheduled for today, and the percentage of
  those completed.
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

* `object_type` -- a string. Will always be "feed"

----
