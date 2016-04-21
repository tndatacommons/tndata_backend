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
    Behavior,
    Category,
    Goal,
    Trigger,
    UserCompletedAction,
)
from .. sequence import get_next_useractions_in_sequence


def _complete_goal(user, title):
    user.usergoal_set.filter(goal__title=title).update(completed=True)


def _complete_behavior(user, title):
    user.userbehavior_set.filter(behavior__title=title).update(completed=True)


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
            return mommy.make(
                Goal,
                title=title,
                sequence_order=seq,
                state='published',
                categories=[category]
            )

        def _behavior(title, goal, seq):  # Function to create a Behavior
            return mommy.make(
                Behavior,
                title=title,
                sequence_order=seq,
                state='published',
                goals=[goal]
            )

        def _action(title, behavior, seq):  # Function to generate an Action
            return mommy.make(
                Action,
                title=title,
                sequence_order=seq,
                behavior=behavior,
                default_trigger=_t(),
                state='published'
            )

        # Create a series of sequenced content.
        # The number in parenthesis indicates the object's sequence_order.
        # ----------------------------------------------------------------
        # GA (0)
        # - BA (0) -- AA (0), AB (0), AC (0)
        # - BB (0) -- AD (0), AE (1), AF (1)
        # - BC (1) -- AG (0), AH (1), AI (1)
        # GB (0)
        # - BD (0) -- AJ (0), AK (1)
        # - BE (1) -- AL (0), AM (1)
        # GC (1)
        # - BF (0) -- AN (0), AO (0)
        # - BG (0) -- AP (0), AQ (0)
        # - BH (1) -- AR (0), AS (0)

        cat = mommy.make(Category, title="C0", order=0, state='published')

        # Goal GA
        ga = _goal('GA', cat, 0)
        ba = _behavior("BA", ga, 0)
        _action("AA", ba, 0)
        _action("AB", ba, 0)
        _action("AC", ba, 0)

        bb = _behavior("BB", ga, 0)
        _action("AD", bb, 0)
        _action("AE", bb, 1)
        _action("AF", bb, 1)

        bc = _behavior("BC", ga, 1)
        _action("AG", bc, 0)
        _action("AH", bc, 1)
        _action("AI", bc, 1)

        # Goal GB
        gb = _goal('GB', cat, 0)
        bd = _behavior('BD', gb, 0)
        _action("AJ", bd, 0)
        _action("AK", bd, 1)

        be = _behavior('BE', gb, 1)
        _action("AL", be, 0)
        _action("AM", be, 1)

        # Goal GC
        gc = _goal('GC', cat, 1)
        bf = _behavior("BF", gc, 0)
        _action("AN", bf, 0)
        _action("AO", bf, 0)

        bg = _behavior('BG', gc, 0)
        _action("AP", bg, 0)
        _action("AQ", bg, 0)

        bh = _behavior("BH", gc, 1)
        _action("AR", bh, 0)
        _action("AS", bh, 0)

        # Enroll the user in all of the above content.
        cat.enroll(cls.user)

    def test_sequencing(self):
        # ensure the user got enrolled
        self.assertEqual(self.user.useraction_set.count(), 19)

        # ---------------------------------------------------------------------
        # The we we'll test this methods is to call it, and verify a list of
        # titles, then change the user's completed actions and do it again.
        # ---------------------------------------------------------------------

        # Starting out.
        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AA', 'AB', 'AC', 'AD', 'AJ', ]
        )

        # Completed AA and AB
        _complete_action(self.user, 'AA')
        _complete_action(self.user, 'AB')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AC', 'AD', 'AJ', ]
        )

        # Completed the rest of the actions with sequence_order = 0
        _complete_action(self.user, 'AC')
        _complete_action(self.user, 'AD')
        _complete_action(self.user, 'AG')
        _complete_action(self.user, 'AJ')
        _complete_action(self.user, 'AL')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AE', 'AF', 'AK']
        )

        # complete the rest of the actions... in BA, BB, BD
        _complete_action(self.user, 'AE')
        _complete_action(self.user, 'AF')
        _complete_action(self.user, 'AJ')
        _complete_action(self.user, 'AK')

        # Complete Behaviors with sequence_order = 0 in Goals with seq = 0
        _complete_behavior(self.user, 'BA')
        _complete_behavior(self.user, 'BB')
        _complete_behavior(self.user, 'BD')

        # Leaving BC, BD active (they both have seq = 1)
        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AH', 'AI', 'AM']
        )

        # Then completing those actions.. as well as their Behaviors/Goals.
        _complete_action(self.user, 'AH')
        _complete_action(self.user, 'AI')
        _complete_action(self.user, 'AM')
        _complete_behavior(self.user, 'BC')
        _complete_behavior(self.user, 'BE')
        _complete_goal(self.user, 'GA')
        _complete_goal(self.user, 'GB')

        # This leaves goal GC, and we start over with Behaviors with seq = 0
        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AN', 'AO', 'AP', 'AQ']
        )

        # Now, complete all of the above actions, and behaviors...
        _complete_action(self.user, 'AN')
        _complete_action(self.user, 'AO')
        _complete_action(self.user, 'AP')
        _complete_action(self.user, 'AQ')
        _complete_behavior(self.user, 'BF')
        _complete_behavior(self.user, 'BG')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AR', 'AS']
        )

        # complete one action
        _complete_action(self.user, 'AS')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            sorted(list(results.values_list("action__title", flat=True))),
            ['AR']
        )

        # complete the rest
        _complete_action(self.user, 'AR')
        _complete_behavior(self.user, 'BH')
        _complete_goal(self.user, 'GC')

        results = get_next_useractions_in_sequence(self.user)
        self.assertEqual(
            list(results.values_list("action__title", flat=True)),
            []
        )
