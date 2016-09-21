
**API Version 2**

This endpoint represents a user's selected goals. That is, it's an object
that defines a mapping between [Users](/api/users/) and
[Goals](/api/goals/).

GET requests to this page will simply list this mapping for the authenticated
user.

## Contents

* <a href="#fields">Fields</a>
* <a href="#adding-a-goal">Adding a Goal </a>
* <a href="#viewing-the-goal-data">Viewing the Goal data </a>
* <a href="#filtering">Filtering </a>
* <a href="#removing-a-goal-from-the-users-list">Removing a Goal from the user's list.</a>
* <a href="#update-a-goal-mapping">Update a Goal Mapping. </a>
* <a href="#additional-information">Additional information</a>

## Fields <a href="#fields">&para;</a>

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserGoal` mapping.
* `user`: The Unique identifier for the `User`
* `goal`: An object that represents the `Goal` selected by the user
* `primary_category`: The ID of the primary category for this goal
* `editable`: A boolean that indicates whether or not a user
* `engagement_15_days`: User's engagment with this goal over the past 15 days
* `engagement_30_days`: User's engagment with this goal over the past 30 days
* `engagement_60_days`: User's engagment with this goal over the past 60 days
* `engagement_rank`: User's engagment with this goal compared to other users
* `created_on`: Time at which the user selected this item.
  should be able to customize the reminders beneath this content
* `object_type`: A string, will always be 'usergoal'

## Adding a Goal <a href="#adding-a-goal">&para;</a>

To associate a Goal with a User, POST to `/api/users/goals/` with the
following data:

    {'goal': GOAL_ID}

Additionally, you may specify a `primary_category` in order to associate
this information with a Category:

    {'goal': GOAL_ID, 'primary_category': CATEGORY_ID}


## Viewing the Goal data <a href="#viewing-the-goal-data">&para;</a>

Additional information for the Goal mapping is available at
`/api/users/goals/{usergoal_id}/`. In this case, `{usergoal_id}` is the
database id for the mapping between a user and a goal.

## Filtering <a href="#filtering">&para;</a>

UserGoals can be filtered using a query string parameter.

* To filter for selected goals that have an action scheduled _today_, use the
  following:  `/api/users/goals/?today=1`
* To filter for specific selected goals, you may provide a goal ID, for
  example: `/api/users/goals/?goal=42`


## Removing a Goal from the user's list. <a href="#removing-a-goal-from-the-users-list">&para;</a>

Send a DELETE request to the usergoal mapping endpoint:
`/api/users/goals/{usergoal_id}/`.

## Update a Goal Mapping. <a href="#update-a-goal-mapping">&para;</a>

Updating a goal mapping is currently not supported.

## Additional information <a href="#additional-information">&para;</a>

The Goals that a User has selected are also available through the
`/api/users/` endpoint as a `goals` object on the user.

----

