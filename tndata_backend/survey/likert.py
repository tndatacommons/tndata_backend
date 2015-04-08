"""
This module contains scales for the various types of Likert questions.

For 5-pt scales: http://goo.gl/BCBGlz
For 7-pt scales: http://goo.gl/CU5R5C



"""
from collections import OrderedDict

# This is a mapping of different types of scales to model choices.
# Note: This is stored as an ordered dict to prevent migrations from generating
# new entries; note how options are added, below.
LIKERT_SCALES = OrderedDict()

# Agreement
LIKERT_SCALES[ "5_point_agreement"] = (
   (1, 'Strongly Disagree'),
   (2, 'Disagree'),
   (3, 'Neither Agree nor Disagree'),
   (4, 'Agree'),
   (5, 'Strongly Agree'),
)

LIKERT_SCALES["5_point_reverse_agreement"] = (
    (5, 'Strongly Disagree'),
    (4, 'Disagree'),
    (3, 'Neither Agree nor Disagree'),
    (2, 'Agree'),
    (1, 'Strongly Agree'),
)

LIKERT_SCALES["7_point_agreement"] = (
    (1, 'Strongly Disagree'),
    (2, 'Disagree'),
    (3, 'Slightly Disagree'),
    (4, 'Neither Agree nor Disagree'),
    (5, 'Slightly Agree'),
    (6, 'Agree'),
    (7, 'Strongly Agree'),
)
LIKERT_SCALES["7_point_reverse_agreement"] = (
    (7, 'Strongly Disagree'),
    (6, 'Disagree'),
    (5, 'Slightly Disagree'),
    (4, 'Neither Agree nor Disagree'),
    (3, 'Slightly Agree'),
    (2, 'Agree'),
    (1, 'Strongly Agree'),
)
LIKERT_SCALES["9_point_agreement"] = (
    (1, 'Extremely Disagree'),
    (2, 'Strongly Disagree'),
    (3, 'Moderately Disagree'),
    (4, 'Slightly Disagree'),
    (5, 'Neither Agree nor Disagree'),
    (6, 'Slightly Agree'),
    (7, 'Moderately Agree'),
    (8, 'Strongly Agree'),
    (9, 'Extremely Agree'),
)
LIKERT_SCALES["9_point_reverse_agreement"] = (
    (9, 'Extremely Disagree'),
    (8, 'Strongly Disagree'),
    (7, 'Moderately Disagree'),
    (6, 'Slightly Disagree'),
    (5, 'Neither Agree nor Disagree'),
    (4, 'Slightly Agree'),
    (3, 'Moderately Agree'),
    (2, 'Strongly Agree'),
    (1, 'Extremely Agree'),
)

# Temporal/Frequency
LIKERT_SCALES["5_point_frequency"] = (
    (1, 'Never'),
    (2, 'Very Rarely'),
    (3, 'Rarely'),
    (4, 'Occasionally'),
    (5, 'Frequently'),
    (6, 'Very Frequently'),
)
LIKERT_SCALES["7_point_frequency"] = (
    (1, 'Never'),
    (2, 'Rarely'),
    (3, 'Occasionally'),
    (4, 'Sometimes'),
    (5, 'Frequently'),
    (6, 'Usually'),
    (7, 'Every Time'),
)

# Importance
LIKERT_SCALES["7_point_importance"] = (
    (1, 'Not at all important'),
    (2, 'Low importance'),
    (3, 'Slightly important'),
    (4, 'Neutral'),
    (5, 'Moderately important'),
    (6, 'Very important'),
    (7, 'Extremely important'),
)

# Satisfaction
LIKERT_SCALES["5_point_satisfaction"] = (
    (1, 'Not at all satisfied'),
    (2, 'Slightly satisfied'),
    (3, 'Moderately satisfied'),
    (4, 'Very satisfied'),
    (5, 'Extremely satisfied'),
)

LIKERT_SCALES["7_point_satisfaction"] = (
    (1, 'Completely dissatisfied'),
    (2, 'Mostly dissatisfied'),
    (3, 'Somewhat dissatisfied'),
    (4, 'Neither satisfied or dissatisfied'),
    (5, 'Somewhat satisfied'),
    (6, 'Mostly satisfied'),
    (7, 'Completely satisfied'),
)

# Necessity
LIKERT_SCALES["5_point_necessary"] = (
    (1, 'Very UNnecessary'),
    (2, 'Somewhat UNnecessary'),
    (3, 'Neither Necessary nor UNnecessary'),
    (4, 'Somewhat Necessary'),
    (5, 'Very Necessary'),
)
