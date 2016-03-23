
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
* `object_type` -- a string. Will always be "feed"

----

** this is a work in progres **

It's an attempt to separate feed data from selected goal data. See also:

* [/api/feed](/api/feed/)  -- another take on this.
* [/api/feed/upcoming/](/api/feed/upcoming/) -- a paginated result of upcoming actions


----
