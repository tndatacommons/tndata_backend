A User's custom goals.  This endpoint allows a user to retrieve a list
of or create new custom goals.

GET requests return an array of results containing the following:

* `id`: The `CustomGoal` ID.
* `user`: The ID for the goal's owner.
* `title`: The title of the custom goal.
* `title_slug`: A sluggified version of the title.
* `updated_on`: Date the goal was updated.
* `created_on`: Date the goal was created.
* `object_type`: This will always be the string, `customgoal`.

## Creating Custom Goals.

Send a POST request to the [/api/users/customgoals/](/api/users/customgoals/)
endpoint with the following information:

    {'title': 'Some Title for your custom goal'}

## Custom Goal Details

You can retrieve details for a single custom goal instance via the
`/api/users/customgoals/{customgoal_id}/` endpoint, which will return a
single JSON representation for the object.

## Updating Custom Goals.

Send a PUT request to the `/api/users/customgoals/{customgoal_id}/` endpoint,
containing the information that you wish to update, namely the title.

    {'title': 'Updated Title'}


## Deleting Custom Goals

Send a DELETE request to the goal's _detail_ endpoint:
`/api/users/customgoals/{customgoal_id}/`. Note that this will also remove all
associated `CustomAction` objects. Successful deletions return a 204 No Content
response.

----

