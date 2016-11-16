
**API Version 2**

Categories are containers for similar Goals, but they may also represent a
_Package_ of goals/actions. A Goal may appear in more than one category.

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
* `featured`: A Boolean value: Indicates whether or not the category should
  be featured in the app.
* `grouping`: An integer that determines how categories should be grouped
  together and how groups should be ordered (lower numbers mean category groups
  should be listed first). A value of `-1` means there is no grouping set.
* `grouping_name`: A name that should be applied to a group.
* `object_type`: Will always be the string `category`.

## Category Endpoints

Each category is available at an endpoint based on it's database ID: `/api/categories/{id}/`.


## Filters

Categories can be filtered by the following attributes:

* `selected_by_default`. e.g. `/api/categories/?selected_by_default=1` will
  list categories that are selected by default, while
  `/api/categories/?selected_by_default=0` will not.
* `featured`. e.g. `/api/categories/?featured=1`
* `organization`. e.g. `/api/categories/?organization=42` will display categories
  associated with the given organization.
* `program`. e.g. `/api/categories/?program=7` will display categories
  associated with the given program.


## Organizations & Programs

Users who are members in an Organization (see `/api/organizations/`) will
receive a slightly different set of results, here. An `Organization` may contain
one or more `Program`s that specify a mapping of categories to the organization.

If a user is a member of an Organization, results from this endpoint will exclude
Categories from other organizations (in which the user is not a member), as
well as any category that has explicently been marked as hidden from
organization members (see the `Category.hidden_from_organizations` field).

Additionally, users who are _not_ members of an organization will not see
Categories that are associated with an organization.


----
