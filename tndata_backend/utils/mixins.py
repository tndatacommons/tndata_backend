from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    """A mixin for a class-based view that requires the user to be logged in.

    Borrowed from: https://goo.gl/CtYx3s

    """

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)
