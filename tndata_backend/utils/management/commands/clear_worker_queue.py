from django.core.management.base import BaseCommand, CommandError
from utils import queue


class Command(BaseCommand):
    help = 'WARNING: Will clear specified jobs from the worker queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help=("Clear ALL jobs from the worker queue")
        )
        parser.add_argument(
            '--failed',
            action='store_true',
            dest='failed',
            default=True,
            help=("Clear only failed jobs (default)")
        )

    def handle(self, *args, **options):
        if options.get('all'):
            which = 'total'
            num = queue.clear_all()
        else:
            which = 'failed'
            num = queue.clear_failed()

        self.stdout.write("\nDeleted {} {} jobs.\n".format(num, which))
