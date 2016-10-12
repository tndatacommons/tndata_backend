This endpoing exposes all of a user's selected goal data. It returns an array
of results containing objects that consist of the following.

## Fields

* `id`: A User's unique DB ID.
* `needs_onboarding`: boolean, whether or not the user needs to go through onboarding
* `places`: an array of `Place` objects.
* `user_categories`: An array of `Usercategory` objects.
* `user_goals`: An array of `UserGoal` objects.
* `user_actions`: An array of `UserAction` objects.


---
