from unittest.mock import patch, call
from django.test import TestCase

from .. decorators import cached_method


class TestCachedMethodDecorator(TestCase):

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCachedMethodDecorator).setUpTestData()

        # A Test class with a cached method.
        class Klass:
            @cached_method("{}-test", timeout=99)
            def meth(self, *args, **kwags):
                return "result"
        cls.Klass = Klass

        # A dummy object that will be used as input to the cached method
        class Obj:
            id = 5
        cls.obj = Obj()

    def test_method_uncached(self):
        """When the method has not been cached, it should set the cache."""
        with patch("utils.decorators.cache") as mock_cache:
            mock_cache.get.return_value = None  # Ensure first call returns None

            k = self.Klass()
            k.meth(self.obj)  # 1st call, cache should get set

            # check for cache calls.
            mock_cache.assert_has_calls([
                call.get("5-test"),
                call.set("5-test", "result", timeout=99),
            ])

    def test_method_cached(self):
        with patch("utils.decorators.cache") as mock_cache:
            mock_cache.get.return_value = "result"  # later calls return a value

            k = self.Klass()
            k.meth(self.obj)  # 2nd call, returns cached result

            mock_cache.assert_has_calls([
                call.get("5-test")
            ])
