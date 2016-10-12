
**API Version 2**

Goals may be associated with multiple categories, and they contain multiple
Actions (Notifications). This enpoint lists an array of published goals.


## Fields

Each goal contains the following information:

* `id`: The unique database identifier for the goal
* `sequence_order`: An integer. The order in which users should receive
  notifications from goals in their selected categories.
* `title`: A unique Title (or name) for the goal.
* `title_slug`: A url-friendly version of the title.
* `description`: A short description for the goal. Plain text (possibly markdown)
* `html_description`: HTML version of the description.
* `icon_url`: A URL for an image associated with the category
* `categories`: A list of [Category](/api/categories/) IDs. These are the
  parent categories for the goal.
* `object_type`: A string; will alwayws be `goal`.

## Goal Details Endpoint

Each goal's content is available at an endpoint based on it's
database ID `/api/goals/{id}/`.

## Enrolling a user in a Goal

You may also enroll a user in a goal, directly. To do so, send a POST reuest
to `/api/goals/{id}/enroll/`, including the following information:

    {
        'category': ID,  // Optional, the parent category's ID.
    }


## Filtering

Goals can be filtered using a querystring paramter. Currently, filtering is
only availble for categories; i.e. You can retrieve goals for a category
by providing a category id: `/api/goals/?category={category_id}`

----
