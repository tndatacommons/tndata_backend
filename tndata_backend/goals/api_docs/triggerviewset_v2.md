
**API Version 2**

A Trigger contains the information that is used to generate the times/dates
for push notifications. It generally contains a date, time, some recurrence
information and additional detaills on when/if notifications should stop.


## Trigger Fields

Triggers contain the following:

* `id`: (read-only) The unique database identifier for the trigger
* `user`: User to which the trigger belongs (will be `null` for this endpoint)
* `name`: A unique name for a trigger.
* `name_slug`: A web-friendly version of the name.
* `time`: for "time" trigger types, the time at which an alert is sent.
* `trigger_date`: (optional) The date on which triggers should start.
* `recurrences`: For "time" triggers, this is an iCalendar (rfc2445) format.
  This field is optional and may be null.
* `recurrences_display`: human-readible information for `recurrences`
* `disabled`: Boolean -- Whether or not this trigger is disabled. Disabled
  triggers will not send notifications.
* `next`: (read-only) Date/Time for the next occurance of this trigger
* `object_type`: Will always be the string, "trigger"

## Trigger Details

Each trigger is available at an endpoint based on it's database ID:
`/api/triggers/{id}/`.

----

