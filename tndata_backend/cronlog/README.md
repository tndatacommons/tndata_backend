cronlog
=======

A simple (in-house) Cron-job reporting app.


When we run cron jobs, we'll dump some data on when they were run and if
they were successful.


Installation
------------

0. Add the code to your project (TODO: put this on pypi?)
1. Add `cronlog` to `INSTALLED_APPS`.
2. Set some value for your `CRONLOG_KEY` in settings.py (create this yourself
   and keep it secret).
3. Add an entry to your Root URLConf (e.g. soemthing like: `url(r'^cronlog/', include('cronlog.urls', namespace='cronlog')),`
4. Schedule the `clear_cronlogs` command to run periodically so you don't
   fill up your database.


Usage
-----

**Viewing log entries**: All log entries are listed in the admin. See
[/admin/cronlog/](/admin/cronlog/) for details.


**Adding log entries**: Use `curl` to insert a `CronLog` entry. This is
intended to be run from a bash script that is called from cron! Here's an example:

    curl
        --data 'message=YOUR MESSAGE&command=YOUR COMMAND&key=CRONLOG_KEY'
        https://example.com/cronlog/add/

You may also specify the host on which the command is run. If omitted, the
value frmo the http host header (or from `USE_X_FORWARDED_HOST` if available)
will be used.

    curl
        --data 'host=SYSTEM&message=YOUR MESSAGE&command=YOUR COMMAND&key=CRONLOG_KEY'
        https://example.com/cronlog/add/

See `views.py` to use the built-in KEY.
