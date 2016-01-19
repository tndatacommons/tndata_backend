A Trigger represents information we send to a user (via a push
notification) to remind them to take an action or think about a behavior.

**NOTE**: This is still a work in progress and subject to change; This
endpoint currently only displayes the set of _default_ triggers; i.e. those
that don't belong to a particular user.

Triggers contain the following:

* id: The unique database identifier for the trigger
* user: User to which the trigger belongs (will be `null` for this endpoint)
* name: A unique name for a trigger.
* name_slug: A web-friendly version of the name.
* time: for "time" trigger types, the time at which an alert is sent.
* recurrences: For "time" triggers, this is an iCalendar (rfc2445) format.
  This field is optional and may be null.
* recurrences_display: human-readible information for `recurrences`
* next: Date/Time for the next occurance of this trigger

## Trigger Endpoints

Each trigger is available at an endpoint based on it's database ID: `/api/triggers/{id}/`.

----

