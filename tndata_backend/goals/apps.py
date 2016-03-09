from django.apps import AppConfig


class GoalsConfig(AppConfig):
    name = 'goals'
    verbose_name = "Goals"

    def ready(self):
        Action = self.get_model('Action')
        Action._add_action_type_creation_urls_to_action()
