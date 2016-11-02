from django.db.models import Manager


class FunContentManager(Manager):

    def random(self, message_type=None):
        """Return a random FunContent instance."""
        if message_type:  # Ensure this is a valid type.
            assert message_type in [m[0] for m in self.model.MESSAGE_TYPE_CHOICES]
            query = (
                "SELECT * FROM rewards_funcontent where message_type=%s "
                "ORDER BY random() LIMIT 1"
            )
            params = [message_type]
        else:
            query = "SELECT * FROM rewards_funcontent ORDER BY random() LIMIT 1"
            params = None

        try:
            return self.raw(query, params)[0]
        except IndexError:
            return None
