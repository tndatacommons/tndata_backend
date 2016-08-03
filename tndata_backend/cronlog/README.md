cronlog
=======

A simple (in-house) Cron-job reporting app.


When we run cron jobs, we'll dump some data on when they were run and if
they were successful.


Usage
-----

**Viewing log entries**: All log entries are listed in the admin. See
[/admin/cronlog/](/admin/cronlog/) for details.


**Adding log entries**: Use `curl` to insert a `CronLog` entry. This is
intended to be run from a bash script that is called from cron! Here's an example:

    curl
        --data 'message=YOUR MESSAGE&command=YOUR COMMAND&key=YOUR KEY'
        https://example.com/cronlog/add/

See `views.py` to use the built-in KEY.
