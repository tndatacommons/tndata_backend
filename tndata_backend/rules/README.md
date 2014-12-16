rules app
=========

This is an app to store _rules_ pertaining to other apps and their models. It's
based on [business-rules](https://github.com/venmo/business-rules) and the
[business-rules-ui](https://github.com/venmo/business-rules-ui) projects.

This app contains:

* Models to store (JSON-encoded?) business rules
* Views to list/create rules
* Hooks into other apps to read *variables* and *actions* (from appname/rules.py)
* A Management command to query/run all rules periodically.


Creating Rules
--------------

For an app to expose variables and actions, there must be a class to do that in
a `rules` module.

*TODO*: Need some way to hook those up here. (a setting? magic?)


License
-------

This code is the property of Tennessee Data Commons.

(c) 2014 all rights reserved.
