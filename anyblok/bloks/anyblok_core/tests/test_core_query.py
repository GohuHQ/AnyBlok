from anyblok.tests.testcase import DBTestCase


class TestException(Exception):
    pass


class TestCoreQuery(DBTestCase):

    def test_update(self):

        def inherit_update():

            from anyblok import Declarations
            Model = Declarations.Model
            Integer = Declarations.Column.Integer

            @Declarations.target_registry(Model)
            class Test:

                id = Integer(primary_key=True)
                id2 = Integer()

                @classmethod
                def sqlalchemy_query_update(cls, query, *args, **kwargs):
                    raise TestException('test')

        registry = self.init_registry(inherit_update)
        try:
            registry.Test.query().update({'id2': 1})
            self.fail('Update must fail')
        except TestException:
            pass

        try:
            t = registry.System.Blok.query().first()
            t.update({'state': 'plop'})
        except TestException:
            pass

    def test_inherit(self):

        def inherit():

            from anyblok import Declarations
            Core = Declarations.Core

            @Declarations.target_registry(Core)
            class Query:

                def foo(self):
                    return True

        registry = self.init_registry(inherit)
        self.assertEqual(registry.System.Blok.query().foo(), True)
