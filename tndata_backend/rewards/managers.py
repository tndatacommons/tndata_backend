from django.db.models import Manager


class FunContentManager(Manager):

    def random(self):
        """Return a random FunContent instance."""
        query = "SELECT * FROM rewards_funcontent ORDER BY random() LIMIT 1"
        return self.raw(query)[0]
