# NOTE: Dont' import any models directly, here; the functions here are called
# from a migration, so let's import from an AppConfig if at all possible.


def _get_group_and_permission(apps):
    """Use the given AppConfig (if available) to import Group and Permission.
    Returns a (Group, Permission) tuple.
    """
    if apps is not None:
        return (
            apps.get_model("auth", "Group"),
            apps.get_model("auth", "Permission")
        )
    else:
        # Just import as normal
        from django.contrib.auth.models import Group, Permission
        return (Group, Permission)
