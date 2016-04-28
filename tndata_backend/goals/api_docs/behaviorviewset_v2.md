
**API Version 2**

A Behavior may reside in one or more goals, and it contains zero or more
Actions.

## Fields

* `id`: The unique database identifier for the behavior
* `title`: A unique, Formal title. Use this to refer to this item.
* `description`: A short description of the Behavior. Plain text (possibly markdown)
* `html_description`: HTML version of the description.
* `more_info`: Additional information displayed when the user drills down
  into the content. Contains markdown.
* `html_more_info`: HTML version of the `more_info` field.
* `external_resource`: A link or reference to an outside resource necessary
  for adoption
* `external_resource_name`: A human-friendly name for the external resource
* `icon_url`: A URL for an icon associated with the category
* `goals`: A list of goal IDs in which this Behavior appears.
* `object_type`: will always be the string `behavior`

## Behavior Endpoints

Each item is available at an endpoint based on it's database ID: `/api/behaviors/{id}/`.

## Filtering

Behaviors can be filtered using a querystring parameter. Currently,
filtering is availble for both goals and categories. You can filter by an
ID or a slug.

* Retrieve all Behaviors that belong to a particular goal:
  `/api/behaviors/?goal={goal_id}` or by slug
  `/api/behaviors/?goal={goal_title_slug}`
* Retrieve all Behaviors that belong to a particular category:
  `/api/behaviors/?category={category_id}` or by slug:
  `/api/behaviors/?category={category_title_slug}`

----

