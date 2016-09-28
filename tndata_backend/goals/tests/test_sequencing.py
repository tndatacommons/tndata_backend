"""
This is essentially a huge integration test to verify that content
sequencing results in the user seeing the correct data based on their
'progress' in responding to notifications.

"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from model_mommy import mommy

from .. models import (
    Action,
    Category,
    Goal,
    Trigger,
    UserCompletedAction,
)
from .. sequence import get_next_useractions_in_sequence


def _complete_goal(user, title):
    user.usergoal_set.filter(goal__title=title).update(completed=True)


def _complete_action(user, action_title):
    # Fetch the UserAction
    ua = user.useraction_set.get(action__title=action_title)

    # Create a UserCompletedAction instance
    UserCompletedAction.objects.create(
        user=user,
        action=ua.action,
        useraction=ua,
        state=UserCompletedAction.COMPLETED
    )


class TestSequencing(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user.
        User = get_user_model()
        cls.user = User.objects.create_user("asdf", "asdf@example.com", "asdf")

        def _t():
            # Function to generate a trigger
            return mommy.make(Trigger, time_of_day='morning', frequency='daily')

        def _goal(title, category, seq):  # Function to create a Goal
            goal = mommy.make(
                Goal,
                title=title,
                sequence_order=seq,
                state='published',
            )
            goal.categories.add(category)
            return goal

        def _action(title, goal, seq):  # Function to generate an Action
            action = mommy.make(
                Action,
                title=title,
                sequence_order=seq,
                default_trigger=_t(),
                state='published'
            )
            action.goals.add(goal)
            return action

        # Create a series of sequenced content.
        # The number in parenthesis indicates the object's sequence_order.
        # ----------------------------------------------------------------
        # GA (0)
        # - AA (0), AB (0), AC (0),
        # - AD (1), AE (1), AF (1),
        # - AG (2), AH (2), AI (2),
        #
        # GB (0)
        # - BJ (0), BK (0)
        # - BL (1), BM (1)
        #
        # GC (1)
        # - CN (0), CO (0)
        # - CP (1), CQ (1)
        # - CR (2), CS (2)

        cat = mommy.make(Category, title="C0", order=0, state='published')

        # Goal GA
        ga = _goal('GA', cat, 0)
        _action("AA", ga, 0)
        _action("AB", ga, 0)
        _action("AC", ga, 0)

        _action("AD", ga, 1)
        _action("AE", ga, 1)
        _action("AF", ga, 1)

        _action("AG", ga, 2)
        _action("AH", ga, 2)
        _action("AI", ga, 2)

        # Goal GB
        gb = _goal('GB', cat, 0)
        _action("BJ", gb, 0)
        _action("BK", gb, 0)

        _action("BL", gb, 1)
        _action("BM", gb, 1)

        # Goal GC
        gc = _goal('GC', cat, 1)
        _action("CN", gc, 0)
        _action("CO", gc, 0)

        _action("CP", gc, 1)
        _action("CQ", gc, 1)

        _action("CR", gc, 2)
        _action("CS", gc, 2)

        # Enroll the user in all of the above content.
        cat.enroll(cls.user)

    def test_sequencing(self):
        # ensure the user got enrolled
        self.assertEqual(self.user.useraction_set.count(), 19)

        # ---------------------------------------------------------------------
        # The way we'll test this methods is to call it, and verify a list of
        # titles, then change the user's completed actions and do it again.
        # ---------------------------------------------------------------------

        # Starting out.
        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AA', 'AB', 'AC', 'BJ', 'BK']
        )

        # Completed AA and AB
        _complete_action(self.user, 'AA')
        _complete_action(self.user, 'AB')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AC', 'BJ', 'BK']
        )

        # Completed the rest of the actions with goal = 0, sequence_order = 0
        _complete_action(self.user, 'AC')
        _complete_action(self.user, 'BJ')
        _complete_action(self.user, 'BK')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AD', 'AE', 'AF', 'BL', 'BM']
        )

        # complete the rest of the actions = 1
        for action in ['AD', 'AE', 'AF', 'BL', 'BM']:
            _complete_action(self.user, action)

        # Leaving actions with order = 2, goal = 0
        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AG', 'AH', 'AI']
        )

        # Then completing those actions.. as well as their Behaviors/Goals.
        for action in ['AG', 'AH', 'AI']:
            _complete_action(self.user, action)
        _complete_goal(self.user, 'GA')
        _complete_goal(self.user, 'GB')

        # This leaves goal GC, and we start over with actions with seq = 0
        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['CN', 'CO']
        )

        # Now, complete all of the above actions
        _complete_action(self.user, 'CN')
        _complete_action(self.user, 'CO')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['CP', 'CQ']
        )

        # complete one action
        _complete_action(self.user, 'CP')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['CQ']
        )

        # complete the rest (including seq = 2)
        for action in ['CQ', 'CR', 'CS']:
            _complete_action(self.user, action)

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            list(results.values_list("action__title", flat=True)),
            []
        )


class TestContentCompletion(TestCase):
    """Ensure that when a user completes all actions in a Goal, the UserGoal
    is marked as completed.

    This work was implemented to support content sequencing so the test
    is included in this module.

    """

    @classmethod
    def setUpTestData(cls):
        # Create a user.
        User = get_user_model()
        cls.user = User.objects.create_user("asdf", "asdf@example.com", "asdf")

        def _t():
            # Function to generate a trigger
            return mommy.make(Trigger, time_of_day='morning', frequency='daily')

        def _goal(title, category, seq):  # Function to create a Goal
            return mommy.make(
                Goal,
                title=title,
                sequence_order=seq,
                state='published',
                categories=[category]
            )

        def _action(title, goal, seq):  # Function to generate an Action
            act = mommy.make(
                Action,
                title=title,
                sequence_order=seq,
                default_trigger=_t(),
                state='published'
            )
            act.goals.add(goal)
            act.save()
            return act

        # Create a series of sequenced content.
        # C0 (0)
        # - GA (0)
        # -- AA (0)
        # -- AB (1)
        # -- AC (2)
        cat = mommy.make(Category, title="C0", order=0, state='published')

        # Goal GA
        ga = _goal('GA', cat, 0)
        _action("AA", ga, 0)
        _action("AB", ga, 1)
        _action("AC", ga, 2)

        # Enroll the user in all of the above content.
        cat.enroll(cls.user)

    def test_completion(self):
        # ensure the user got enrolled, and that nothing is yet completed
        self.assertEqual(self.user.useraction_set.count(), 3)
        self.assertFalse(
            self.user.usergoal_set.get(goal__title='GA').completed)

        ucas = self.user.usercompletedaction_set.all()
        ucas = ucas.filter(action__title__in=['AA', 'AB', 'AC'])
        self.assertFalse(ucas.exists())

        # Complete an action, the goal is not yet completed.
        _complete_action(self.user, 'AA')
        self.assertFalse(
            self.user.usergoal_set.get(goal__title='GA').completed)

        # Complete the remaining actions...
        for action in ['AB', 'AC']:
            _complete_action(self.user, action)

        # Verify they're completed
        ucas = self.user.usercompletedaction_set.all()
        ucas = ucas.filter(action__title__in=['AA', 'AB', 'AC'])
        self.assertTrue(ucas.exists())

        # AND that the goal got marked as completed.
        self.assertTrue(
            self.user.usergoal_set.get(goal__title='GA').completed)
