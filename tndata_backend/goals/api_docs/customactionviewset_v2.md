
**API Version 2**

A User's custom actions. This endpoint allows a user to retrieve a list
of or create new custom actions. A `CustomAction` object must be associated
with a parent `CustomGoal` object (see [Custom Goals](/api/users/customgoals/))
*OR* with a publicly available `Goal` ([/api/goals/](/api/goals/)).

GET requests return an array of results containing the following:

* `id`: The ID of the `CustomAction` object.
* `user`: The ID of the action's owner.
* `customgoal`: The ID of the parent `CustomGoal` object (may be `null`).
* `goal`: The ID of the parent `Goal` object (may be `null`).
* `goal_title`: The title text of either the related `CustomGoal` or `Goal`.
* `title`: Title of the custom action (required).
* `title_slug`: sluggified version of the title.
* `notification_text`: Text that will be used in a notification (required).
* `custom_trigger`: A `Trigger` object.
* `next_trigger_date`: The next date the notification will be sent.
  May be `null`.
* `prev_trigger_date`: The previous date the notficiation was sent.
  May be `null`.
* `updated_on`: Date the action was last updated.
* `created_on`: Date the action was created.
* `object_type`: Will always be the string, `customaction`.

## Filtering

You may filter the result of listing custom actions by their parent goals. To
do so, include a querystring parameter of `customgoal` or `goal` that includes
either the goal's database ID or title slug.

* `/api/users/customactions/?customgoal={id}`
* `/api/users/customactions/?customgoal={title_slug}`
* `/api/users/customactions/?goal={id}`
* `/api/users/customactions/?goal={title_slug}`

## Creating Custom Actions

Send a POST request to the
[/api/users/customactions/](/api/users/customactions/) endpoint with the
following data:

    {
        'title': 'Your action Title',
        'notification_text': 'Your action's notification',
        'customgoal': {ID of the parent custom goal},
    }

Or add a custom action associated with a public Goal:

    {
        'title': 'Your action Title',
        'notification_text': 'Your action's notification',
        'goal': {ID of the goal},
    }

## Custom Action Details

You can retrieve details for a single custom action instance via the
`/api/users/customactions/{customaction_id}/` endpoint, which will return a
single JSON representation for the object.

## Updating Custom Actions.

Send a PUT request to the `/api/users/customactions/{customaction_id}/`
endpoint, containing the information that you wish to, e.g.:

    {
        'title': 'Updated Title',
        'notification_text': 'Updated notification',
        'customgoal': {ID of the parent custom goal},
    }

## Including a Custom Trigger

CustomActions may be updated in order to set custom Triggers (aka
reminders) for the associated action.

To do this, send a PUT request to the detail url
(`api/users/customactions/{customaction_id}`) with the following information:

* `custom_trigger_time`: The time at which the reminder should fire, in
  `hh:mm` format, in the user's local time.
* `custom_trigger_date`: (optional). For a one-time reminder, this can
  include a date string (yyyy-mm-dd) to define the date at which a reminder
  should next fire. The date should be relative to the user's local time.
* `custom_trigger_rrule`: A Unicode RFC 2445 string representing the days &amp;
  frequencies at which the reminder should occur.

## Completing Custom Action

You can specify that you've completed a custom action (typically from a
reminder) via the `/api/users/customactions/{customaction_id}/complete/`
endpoint. Submit a POST request with the following information:

    {'state': 'completed'}

Where `state` is one of:

* `uncompleted`
* `completed`
* `dismissed`
* `snoozed`

## Custom Action Feedback

You can provide open-ended feedback on a Custom Action by sending a POST
request to the `/api/users/customactions/{customaction_id}/feedback/`
endpoint. Submit a POST request with the following information:

    {'text': 'User-supplied text'}


## Deleting Custom Actions

Send a DELETE request to the custom action's _detail_ endpoint:
`/api/users/customactions/{customaction_id}/`. Successful deletions return a
204 No Content response.

----

