import csv

from django.core.management.base import BaseCommand, CommandError
from rewards.models import FunContent


class Command(BaseCommand):
    """A command to import data from a CSV file into the `FunContent` model.
    This command is fairly flexible, letting you read content from one or more
    columns, and specifying which colums should be used for which fields.

    Run manage.py help load_reward_content for more info.

    Examples of input for the various flags:

     --message 2:4
        will include columns 2, 3, and 4 in the message column

     --message 2 --author 3
        will load column 2 into message, column 3 into author

     --kewords 2
        will load all of the text from column 2 into the keywords field

    The type and message options are required, the rest are optional.

    """
    help = 'Import data from a CSV file for the Fun Content rewards model.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', nargs=1, type=str)

        parser.add_argument(
            '-t',
            '--type',
            action='store',
            type=str,
            dest='message_type',
            default='',
            required=True,
            help='Type of content: quote|fortune|fact|joke'
        )
        parser.add_argument(
            '-m',
            '--message',
            action='store',
            type=str,
            dest='message_columns',
            default=None,
            required=True,
            help='Column number or range (eg "2:4") for the message'
        )
        parser.add_argument(
            '-a',
            '--author',
            action='store',
            type=int,
            dest='author_column',
            default=None,
            help='Column number for the author or attribution.'
        )
        parser.add_argument(
            '-k',
            '--keywords',
            action='store',
            type=int,
            dest='keyword_column',
            default=None,
            help='Column number for the keywords'
        )
        parser.add_argument(
            '-d',
            '--delimiter',
            action='store',
            type=str,
            dest='keyword_delimiter',
            default=',',
            help='A keyword delimiter for columns with multiple keywords. '
                 'The default is a comma.'
        )
        parser.add_argument(
            '-s',
            '--separator',
            action='store',
            type=str,
            dest='message_separator',
            default='\n',
            help='Separator used between message text in multiple columns. '
                 'The defalut is a newline.'
        )

    def handle(self, **options):
        # Check the options input
        csv_path = options['csv_path'][0]
        kw_delimiter = options['keyword_delimiter']
        kw_column = options['keyword_column']
        author_column = options['author_column']
        message_type = options['message_type'].lower()
        message_separator = options['message_separator']
        try:
            message_columns = [int(c) for c in options['message_columns'].split(':')]
            if len(message_columns) == 1:
                message_start = message_columns[0]
                message_end = message_columns[0] + 1
            else:
                message_start, message_end = message_columns
                message_end = message_end + 1  # be inclusive
        except ValueError:
            err = "Invalid input for message column(s): '{}'".format(
                options['message_columns']
            )
            raise CommandError(err)

        if message_type not in [t[0] for t in FunContent.MESSAGE_TYPE_CHOICES]:
            err = "{} is not a valid message type".format(message_type)
            raise CommandError(err)

        created = 0
        with open(csv_path, newline='') as csvfile:
            for row in csv.reader(csvfile):
                message = row[message_start:message_end]
                message = message_separator.join(message)
                if message:  # no content, so skip this...

                    keywords = []
                    if kw_column:
                        keywords = row[kw_column]
                        if kw_delimiter:
                            keywords = keywords.split(kw_delimiter)
                        else:
                            keywords = [keywords]

                    author = ''
                    if author_column:
                        author = row[author_column]

                    FunContent.objects.create(
                        message_type=message_type,
                        message=message,
                        author=author,
                        keywords=keywords
                    )
                    created += 1

        self.stdout.write("Created {} items.".format(created))
