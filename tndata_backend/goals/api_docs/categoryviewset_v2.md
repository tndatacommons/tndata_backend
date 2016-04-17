Categories are containers for similar Goals, but they may also represent a
_Package_ of goals/behaviors/actions. A Goal may appear in more than one category.

Each Category has at least the following bits of information:

* `id`: The unique database identifier for the category
* `order`: Controls the order in which Categories are displayed.
* `title`: The unique Title (or name) of the Category
* `description`: A short description of this Category. Plain text (possibly markdown)
* `html_description`: HTML version of the description.
* `icon_url`: A URL for a square image. This is the category's Icon.
* `image_url`: A URL for a larger image associated with the category. Use as the
  category's _hero_ image above each tab.
* `color`: A primary color for content in this category
* `secondary_color`: A secondary color for content
* `packaged_content`: True or False. Is this category a package.
* `selected_by_default`: If True, this category (and all of its content) will
  be auto-selected for new users when they sign up for the service.
* `object_type`: Will always be the string `category`.

## Category Endpoints

Each category is available at an endpoint based on it's database ID: `/api/categories/{id}/`.


## Filters

Categories can be filtered by the following attributes:

* `selected_by_default`. e.g. `/api/categories/?selected_by_default=1` will
  list categories that are selected by default, while
  `/api/categories/?selected_by_default=0` will not.


----
