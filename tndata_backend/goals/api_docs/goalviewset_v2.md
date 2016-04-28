
**API Version 2**

Goals may be associated with multiple categories, and may contain multiple
Behaviors. This enpoint lists an array of published goals.


## Fields

Each goal contains the following information:

* `id`: The unique database identifier for the goal
* `sequence_order`: An integer. The order in which users should receive
  notifications from goals in their selected categories.
* `title`: A unique Title (or name) for the goal.
* `title_slug`: A url-friendly version of the title.
* `description`: A short description for the goal. Plain text (possibly markdown)
* `html_description`: HTML version of the description.
* `outcome`: Additional (optional) text that may describe an expected outcome
  of pursing this Goal.
* `icon_url`: A URL for an image associated with the category
* `behaviors_count`: The number of behaviors in this goal.
* `categories`: A list of [Category](/api/categories/) IDs. These are the
  parent categories for the goal.
* `object_type`: A string; will alwayws be `goal`.

## Goal Details Endpoint

Each goal's content is available at an endpoint based on it's
database ID `/api/goals/{id}/`.

## Enrolling a user in a Goal

You may also enroll a user in a goal, directly.

## Filtering

Goals can be filtered using a querystring paramter. Currently, filtering is
only availble for categories; i.e. You can retrieve goals for a category
by providing a category id: `/api/goals/?category={category_id}`

----
