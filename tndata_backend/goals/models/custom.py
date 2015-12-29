"""
Models for user-created, Custom Goals & Actions.

-------------------------------------------------------------------------------

CustomGoal:
- user
- title
- updated
- created

CustomAction
- user
- customgoal
- trigger
- text/title
- updated
- created

UserCompletedCustomAction (like UserCompletedAction?)
- (state of completion)?
- custom action
- custom goal

CustomActionFeedback
- text input on how the user is completing their custom goal?
- date added
- custom_action
- custom_goal

-------------------------------------------------------------------------------
"""
