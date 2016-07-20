The User Feed of information: home-feed data for the user, include:

* `next_action`: a `UserAction` object (the mapping between a User and
  an `Action`. This is the upcoming activity for the user.
* `progress` -- an object containing the number of actions completed today,
  the number of total actions scheduled for today, and the percentage of
  those completed.
* `upcoming_actions` -- a list of the `UserAction`s that are relevant for
  today (i.e. the user has a reminder scheduled for today)
* `suggestions` -- a list of suggested `Goal`s for the user.

----

