"""An Action is a concrete action that an person can perform.

Each Action object contains the following:

* id: The unique database identifier for the action
* sequence_order: The order in which actions should be displayed/performed (if any)
* title: A unique, Formal title. Use this to refer to this item.
* title_slug: A url-friendly version of title.
* description: A short description of the Action. Plain text (possibly markdown)
* html_description: HTML version of the description.
* more_info: Additional information displayed when the user drills down
  into the content. Contains markdown.
* html_more_info: HTML version of the `more_info` field.
* external_resource = A link or reference to an outside resource necessary for adoption
* external_resource_name = A human-friendly name for the external resource
* default_trigger: A trigger/reminder for this action. See the
    [Trigger](/api/triggers/) endpoint for more details. The time included
    in this trigger contains no timezone information, so it's safe to assume
    it's always in the user's local time.
* notification_text: Text of the message delivered through notifications
* icon_url: A URL for an icon associated with the category
* image_url: (optional) Possibly larger image for this item.

## Action Endpoints

Each item is available at an endpoint based on it's database ID: `/api/actions/{id}/`.

## Filtering

Actions can be filtered using a querystring parameter. Currently,
filtering is availble for goals, categories. You can filter
by an ID or a slug.

* Retrieve all *Action*s that belong to a particular goal:
  `/api/actions/?goal={goal_id}`, or by slug:
  `/api/actions/?goal={goal_title_slug}`
* Retrieve all *Action*s that belong to a particular category:
  `/api/actions/?category={category_id}`, or by slug:
  `/api/actions/?category={category_title_slug}`

----


