"""
Labels to classify items in our surveys.

"""


def get_label_choices():
    """Return choices for our Survey lablels. These items correspond to some
    of the categories created in the 'goals' app, but we don't read these from
    the DB, otherwise we'll generate new migrations all the time.
    """

    return tuple(sorted((
        ('community', 'Community'),
        ('education', 'Education'),
        ('family', 'Family'),
        ('fun', 'Fun'),
        ('happiness', 'Happiness'),
        ('health', 'Health'),
        ('home', 'Home'),
        ('parenting', 'Parenting'),
        ('prosperity', 'Prosperity'),
        ('romance', 'Romance'),
        ('safety', 'Safety'),
        ('skills', 'Skills'),
        ('wellness', 'Wellness'),
        ('work', 'Work'),
    )))
