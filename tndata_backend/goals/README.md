goals app
=========

This app stores information related to personal Goals.


License
-------

This code is the property of Tennessee Data Commons.

(c) 2014 all rights reserved.


Workflow
--------

The following are notes on new workflow additions:

**Groups of Users**

* Content Creators: Internal or External users who create content
  (Goals/Behaviors/Actions)
* Editors/Publishers: Internal users who can review and publish content


**Content States**

NOTE: Use [django-fsm](https://github.com/kmmbvnr/django-fsm) for states.
Once created, a piece of content can be in one of the following states:

* Draft: Content is being created.
* Review: Content has been submitted for review and publish
* Declined: Content is not suitbable for publishing and/or needs adjustment.
* Published: Content is Available to the public via our api


**Permissions**

* Content Creators can _view_ all content (even unpulished content from others)
* Content Creators can _create_ new content in Draft
* Content Creators can _update_ content in Draft
* Content Creators can _change_ content state to Review.
* Content Creators can _delete_ their own content while in Draft/Review.
* Editors can do all of the above.
* Editors can _update_ content (but not Draft owned by someone else)
* Editors can _delete_ content (but not Draft owned by someone else?)
* (Dashboard) Editors can view a list of all content in Review.
* (Dashboard) Editors can Publish content in Review
* (Dashboard) Editors can change content state to Declined (include a message?)
