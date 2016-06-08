# badgify_api

This app implements a tiny Django-Rest-Framework API around `badgify`,
so users can retrieve a list of their awarded Badges.


## ViewSets

- `AwardViewSet` provides a list of the authenticated user's awards (inluding
  the badges).
- `BadgeViewSet` lists all available badges.
