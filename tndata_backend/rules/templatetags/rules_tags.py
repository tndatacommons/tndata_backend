from django import template
from django.template.defaultfilters import pprint

register = template.Library()


@register.filter(is_safe=True)
def format_rule(rule, prop=None):
    """Given a `Rule` object, display the given property, and pprint it.

    This should primarily be used to display JSON conditions/actions in html.

    """
    if prop not in ['conditions', 'actions', None]:
        return ''

    if prop is None:
        # Just build all the rules
        rule_data = rule.build_rules()
    else:
        prop = "_{0}".format(prop)
        rule_data = getattr(rule, prop)

    return pprint(rule_data)
