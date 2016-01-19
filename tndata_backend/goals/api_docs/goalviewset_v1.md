Goals contain the following information:

* id: The unique database identifier for the goal
* title: A unique Title (or name) for the goal.
* title_slug: A url-friendly version of the title.
* description: A short description for the goal. Plain text (possibly markdown)
* html_description: HTML version of the description.
* outcome: Additional (optional) text that may describe an expected outcome
  of pursing this Goal.
* icon_url: A URL for an image associated with the category
* categories: A list of [Categories](/api/categories/) in which the goal appears.

## Goal Endpoints

Each goal is available at an endpoint based on it's database ID: `/api/goals/{id}/`.

## Filtering

Goals can be filtered using a querystring paramter. Currently, filtering is
only availble for categories; i.e. You can retrieve goals for a category
by providing a category id: `/api/goals/?category={category_id}`

----
