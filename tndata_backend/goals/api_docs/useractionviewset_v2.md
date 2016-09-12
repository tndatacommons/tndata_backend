
**API Version 2**

This endpoint represents a user's selected Actions. That is, an object that
defines a mapping between [Users](/api/users/) and [Actions](/api/actions/).

GET requests to this page will list the `UserAction` objects belonging
to the authenticated user.

## Contents

* <a href="#fields">Fields </a>
* <a href="#adding-a-useraction">Adding a UserAction</a>
* <a href="#adding-a-useraction-and-all-parent-objects-at-once">Adding a UserAction and all parent objects at once</a>
* <a href="#viewing-useractions">Viewing UserActions</a>
* <a href="#deleting-a-useraction">Deleting a UserAction</a>
* <a href="#update-a-useraction">Update a UserAction / Custom Triggers</a>
* <a href="#filtering">Filtering  </a>
* <a href="#additional-information">Additional information</a>
* <a href="#completing-actions-or-not">Completing Actions (or not)</a>

----

## Fields <a href="#fields">&para;</a>

This endpoint returns resources with the following fields.

* `id`: A unique identifier for the `UserAction`
* `user`: A unique identifier for the `User`
* `action`: An object that represents the `Action` selected by the user
* `trigger`: An object that represent's the user's created `Trigger` or the
  default trigger associated with the Action (i.e. information about when
  notifications for this action should be sent). It will contain the following
  additional data:

      - `id`: Unique ID of the Trigger
      - `name`: The trigger's name
      - `trigger_date`: Date on which the trigger shoudl start
      - `time`: Time at which the trigger should fire
      - `recurrences`: an RFC 2445 RRULE string (or null)
      - `recurrences_display`: a human-readable version of recurrences
      - `disabled`: whether or not the trigger is disabled.

* `next_reminder`: a date/time in the user's local timezone for the
  next push notification for this action (may be null if nothing is scheduled)
* `editable`: A boolean that indicates whether or not a user
  should be able to customize the reminders for this action.
  `Action`'s parent `Behavior`.
* `goal_title`: A string, the title of the primary-goal.
* `goal_description`: A string, the description from the primary-goal.
* `userbehvaior_id`: The ID of the `UserBehavior` object associated with the
* `primary_goal`: The ID of the goal under which the user selected this action.
* `primary_usergoal`: The ID of the `UserGoal` related to the `primary_goal`.
* `primary_category`: The ID of the category associated with this action.
* `created_on`: Time at which the user selected this item.
* `object_type`: A string that will always be `useraction`

## Adding a UserAction <a href="#adding-a-useraction">&para;</a>

To associate a Action with a User, POST to `/api/users/actions/` with the
following data (the action the user is selecting, and (optionally) the
parent goal and category for the action).

    {
        'action': ACTION_ID,
        'primary_goal': GOAL_ID,         # (optional)
        'primary_category': CATEGORY_ID  # (optional)
    }

## Adding a UserAction and all parent objects at once <a href="#adding-a-useraction-and-all-parent-objects-at-once">&para;</a>

If you submit a `category`, `goal`, `behavior`, and `action` all in a single
payload, each object will be added to the user's collection at once; This will
simplify adding the tree of data. When using this payload, all items are required,
and the given `goal` and `category` IDs will be set as the `primary_goal` and
`primary_category`:

    {
        'action': ACTION_ID,
        'behavior': BEHAVIOR_ID,
        'goal': GOAL_ID,
        'category': CATEGORY_ID
    }

## Viewing UserActions  <a href="#viewing-useractions">&para;</a>

Additional information for the UserAction is available at
`/api/users/actions/{useraction_id}/`. In this case, `{useraction_id}`
is the database id for the mapping between a user and a action.

## Deleting a UserAction <a href="#deleting-a-useraction">&para;</a>

Send a DELETE request to the useraction endpoint:
`/api/users/actions/{useraction_id}/`.

## Update a UserAction / Custom Triggers <a href="#update-a-useraction">&para;</a>

UserActions may be updated in order to set custom Triggers (aka
reminders) for the associated action.

To do this, send a PUT request to the detail url
(`api/users/actions/{useraction_id}`) with the following information:

* `custom_trigger_time`: The time at which the reminder should fire, in
  `hh:mm` format, in the user's local time.
* `custom_trigger_date`: (optional). For a one-time reminder, this can
  include a date string (yyyy-mm-dd) to define the date at which a reminder
  should next fire. The date should be relative to the user's local time.
* `custom_trigger_rrule`: A Unicode RFC 2445 string representing the days &amp;
  frequencies at which the reminder should occur.
* `custom_trigger_disabled`: (optional) A `true` or `false` value; if `true`
  the trigger will be disabled.

## Filtering  <a href="#filtering">&para;</a>

UserActions can be filtered using a query string parameter. Currently,
filtering is availble for Goals, Behaviors, Actions, and for Actions
whose notification is scheduled during the current day.

To filter for actions scheduled _today_, use the following:

* `/api/users/actions/?today=1`

For the following examples, you may filter using a numeric ID or a titl slug.
UserActions may be filtered by their parent Category, Goal, Behavior or by
the associated Action. Examples:

* `/api/users/actions/?category={category_id}`
* `/api/users/actions/?category={category_title_slug}`
* `/api/users/actions/?goal={goal_id}`
* `/api/users/actions/?goal={goal_title_slug}`
* `/api/users/actions/?behavior={behavior_id}`
* `/api/users/actions/?behavior={behavior_title_slug}`
* `/api/users/actions/?action={action_id}`
* `/api/users/actions/?action={action_title_slug}`

**NOTE**: Action titles are not unique, so filtering by the `Action.title_slug`
may return multiple results.

## Additional information <a href="#additional-information">&para;</a>

The Actions that a User has selected are also available through the
`/api/users/` endpoint as a `actions` object on the user.

## Completing Actions (or not)  <a href="#completing-actions-or-not">&para;</a>

A User may wish to indicate that they have performed (or completed),
dismissed, snoozed, or have decided not to complete an action. To save this
information:

* send a POST request to `/api/users/actions/{useraction_id}/complete/`
  with a body containing a `state` and an optional `length`; these values
  tell us how the user responded to the action, and how long they snoozed
  the action (if that's what they did).

        {
            'state': 'snoozed', # or 'completed', 'uncompleted', 'dismissed'
            'length': '1hr'     # or  "1d", "custom", "location"
        }

* A 200 response indicates that the action has been updated or created. If
  updated, the response will be: `{updated: <object_id>}`, if created:
  `{created: <object_id>}`.

----

