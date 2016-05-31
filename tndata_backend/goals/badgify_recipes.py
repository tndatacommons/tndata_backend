"""
Badgify Recipes.

See: https://github.com/ulule/django-badgify

"""


from badgify.recipe import BaseRecipe
import badgify


class PythonLoverRecipe(BaseRecipe):
    pass


class JSLoverRecipe(BaseRecipe):
    pass


# Per class
badgify.register(PythonLoverRecipe)
badgify.register(JSLoverRecipe)

# All at once in a list
badgify.register([PythonLoverRecipe, JSLoverRecipe])
