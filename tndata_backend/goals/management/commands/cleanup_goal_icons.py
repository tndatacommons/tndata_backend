from django.core.management.base import BaseCommand
from goals.models import Goal, Behavior


class Command(BaseCommand):
    """We have the ability to convert Actions -> Behaviors, and
    Behaviors -> Goals. However, the first time we did this, we attempted to
    copy the associated icon/image data, and this didn't work out so well.

    This command will clean that up.

    """
    help = 'Removes broken icons/images from Goals & Behaviors due to conversion'

    def _test_file(self, obj, attr_name):
        try:
            # We seem to have an icon/image associated w/ the object.
            if(getattr(obj, attr_name, False)):
                # But accessing it's file data results in an OSError,
                # because it's really a None-type
                getattr(obj, attr_name).file

        except OSError as e:
            msg = "\n{0}) {1}\nError: {2}\n...deleting".format(obj.id, obj, e)
            self.stdout.write(msg)

            # delete the icon & save the object.
            self.removed.append("{0}".format(getattr(obj, attr_name)))
            getattr(obj, attr_name).delete()
            obj.save()

    def clean_category_icons(self):
        for c in Category.objects.all():
            self._test_file(c, 'icon')
            self._test_file(c, 'image')

    def clean_behavior_icons(self):
        for b in Behavior.objects.all():
            self._test_file(b, "icon")
            self._test_file(b, "image")

    def clean_goal_icons(self):
        for g in Goal.objects.all():
            self._test_file(g, "icon")

    def handle(self, *args, **options):
        self.removed = []
        self.clean_goal_icons()
        self.clean_behavior_icons()

        if len(self.removed) > 0:
            self.stdout.write("Cleaned up the following missing files:")
            for f in self.removed:
                self.stdout.write("- {0}".format(f))
