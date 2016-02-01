A User's custom actions. This endpoint allows a user to retrieve a list
of or create new custom actions. A `CustomAction` object must be associated
with a parent `CustomGoal` object (see [Custom Goals](/api/users/customgoals/)).

GET requests return an array of results containing the following:

* `id`: The ID of the `CustomAction` object.
* `user`: The ID of the action's owner
* `customgoal`: The ID of the parent `CustomGoal` object.
* `title`: Title of the custom action (required)
* `title_slug`: sluggified version of the title
* `notification_text`: Text that will be used in a notification (required)
* `custom_trigger`: A `Trigger` object
* `next_trigger_date`: The next date the notification will be sent.
  May be `null`
* `prev_trigger_date`: The previous date the notficiation was sent.
  May be `null`
* `updated_on`: Date the action was last updated.
* `created_on`: Date the action was created.
* `object_type`: Will always be the string, `customaction`.


## Creating Custom Actions

Send a POST request to the
[/api/users/customactions/](/api/users/customactions/) endpoint with the
following data:

    {
        'title': 'Your action Title',
        'notification_text': 'Your action's notification',
        'customgoal': {ID of the parent custom goal},
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

