# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from random import random
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


class TestCache(DBTestCase):

    def add_model_with_method_cached(self):

        from anyblok import Declarations

        @register(Model)
        class Test:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

    def test_cache_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        nb_invalidation = Cache.query().count()
        Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Cache.query().count(), nb_invalidation + 1)

    def test_invalid_cache_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        try:
            Cache.invalidate('Model.Test2', 'method_cached')
            self.fail('No watchdog for bad invalidation cache')
        except Declarations.Exception.CacheException:
            pass

    def test_detect_cache_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        self.assertEqual(Cache.detect_invalidation(), False)
        Cache.insert(registry_name="Model.Test", method="method_cached")
        self.assertEqual(Cache.detect_invalidation(), True)

    def test_get_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        Cache.insert(registry_name="Model.Test", method="method_cached")
        caches = Cache.get_invalidation()
        self.assertEqual(len(caches), 1)
        cache = caches[0]
        self.assertEqual(cache.indentify, ('Model.Test', 'method_cached'))


class TestSimpleCache(DBTestCase):

    def check_method_cached(self, Model, registry_name, value=1):
        m = Model()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate(registry_name, 'method_cached')
        self.assertEqual(m.method_cached(), 2 * value)

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

    def add_model_with_method_cached_by_core(self):

        @register(Core)
        class Base:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self):

        @register(Mixin)
        class MTest:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def add_model_with_method_cached_with_mixin_and_or_core(self,
                                                            withmodel=False,
                                                            withmixin=False,
                                                            withcore=False):

        @register(Core)
        class Base:

            x = 0

            if withcore:
                @Declarations.cache()
                def method_cached(self):
                    self.x += 1
                    return self.x

            else:
                def method_cached(self):
                    self.x += 1
                    return self.x

        @register(Mixin)
        class MTest:

            y = 0

            if withmixin:
                @Declarations.cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()

            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()

        @register(Model)
        class Test(Mixin.MTest):

            z = 0

            if withmodel:
                @Declarations.cache()
                def method_cached(self):
                    self.z += 3
                    return self.z + super(Test, self).method_cached()
            else:
                def method_cached(self):
                    self.z += 3
                    return self.z + super(Test, self).method_cached()

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_model_mixin_core_not_cache(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 11)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 17)

    def test_model_mixin_core_only_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_model_mixin_core_only_model(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 6)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core_and_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)


class TestClassMethodCache(DBTestCase):

    def check_method_cached(self, Model, registry_name):
        m = Model
        value = m.method_cached()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate(registry_name, 'method_cached')
        self.assertNotEqual(m.method_cached(), value)

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @Declarations.classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

    def add_model_with_method_cached_by_core(self):

        @register(Core)
        class Base:

            x = 0

            @Declarations.classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self):

        @register(Mixin)
        class MTest:

            x = 0

            @Declarations.classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def add_model_with_method_cached_with_mixin_and_or_core(self,
                                                            withmodel=False,
                                                            withmixin=False,
                                                            withcore=False):

        @register(Core)
        class Base:

            x = 0

            if withcore:
                @Declarations.classmethod_cache()
                def method_cached(cls):
                    cls.x += 1
                    return cls.x

            else:
                @classmethod
                def method_cached(cls):
                    cls.x += 1
                    return cls.x

        @register(Mixin)
        class MTest:

            y = 0

            if withmixin:
                @Declarations.classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()

            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()

        @register(Model)
        class Test(Mixin.MTest):

            z = 0

            if withmodel:
                @Declarations.classmethod_cache()
                def method_cached(cls):
                    cls.z += 3
                    return cls.z + super(Test, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.z += 3
                    return cls.z + super(Test, cls).method_cached()

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_model_mixin_core_not_cache(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 11)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 17)

    def test_model_mixin_core_only_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_model_mixin_core_only_model(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 6)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core_and_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)


class TestInheritedCache(DBTestCase):

    def check_method_cached(self, Model):
        m = Model()
        self.assertEqual(m.method_cached(), 3)
        self.assertEqual(m.method_cached(), 5)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 8)

    def check_inherited_method_cached(self, Model):
        m = Model()
        self.assertEqual(m.method_cached(), 3)
        self.assertEqual(m.method_cached(), 3)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 6)

    def add_model_with_method_cached(self, inheritcache=False):

        @register(Model)
        class Test:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)  # noqa
        class Test:

            y = 0

            if inheritcache:
                @Declarations.cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Test, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Test, self).method_cached()

    def add_model_with_method_cached_by_core(self, inheritcache=False):

        @register(Core)
        class Base:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Core)  # noqa
        class Base:

            y = 0

            if inheritcache:
                @Declarations.cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Base, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Base, self).method_cached()

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self, inheritcache=False):

        @register(Mixin)
        class MTest:

            x = 0

            @Declarations.cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)  # noqa
        class MTest:

            y = 0

            if inheritcache:
                @Declarations.cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test)

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached,
                                      inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test)

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test)

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)


class TestInheritedClassMethodCache(DBTestCase):

    def check_method_cached(self, Model):
        self.assertEqual(Model.method_cached(), 3)
        self.assertEqual(Model.method_cached(), 5)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Model.method_cached(), 8)

    def check_inherited_method_cached(self, Model):
        self.assertEqual(Model.method_cached(), 3)
        self.assertEqual(Model.method_cached(), 3)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Model.method_cached(), 6)

    def add_model_with_method_cached(self, inheritcache=False):

        @register(Model)
        class Test:

            x = 0

            @Declarations.classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)  # noqa
        class Test:

            y = 0

            if inheritcache:
                @Declarations.classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Test, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Test, cls).method_cached()

    def add_model_with_method_cached_by_core(self, inheritcache=False):

        @register(Core)
        class Base:

            x = 0

            @Declarations.classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Core)  # noqa
        class Base:

            y = 0

            if inheritcache:
                @Declarations.classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Base, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Base, cls).method_cached()

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self, inheritcache=False):

        @register(Mixin)
        class MTest:

            x = 0

            @Declarations.classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)  # noqa
        class MTest:

            y = 0

            if inheritcache:
                @Declarations.classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test)

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached,
                                      inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test)

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test)

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)


class TestComparatorInterModel(DBTestCase):

    def check_comparator(self, registry):
        Test = registry.Test
        Test2 = registry.Test2
        self.assertEqual(Test.method_cached(), Test.method_cached())
        self.assertEqual(Test2.method_cached(), Test2.method_cached())
        self.assertNotEqual(Test.method_cached(), Test2.method_cached())

    def test_model(self):

        def add_in_registry():

            @register(Model)
            class Test:

                @Declarations.classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test2:

                @Declarations.classmethod_cache()
                def method_cached(cls):
                    return random()

        registry = self.init_registry(add_in_registry)
        self.check_comparator(registry)

    def test_mixin(self):

        def add_in_registry():

            @register(Mixin)
            class MTest:

                @Declarations.classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test(Mixin.MTest):
                pass

            @register(Model)
            class Test2(Mixin.MTest):

                pass

        registry = self.init_registry(add_in_registry)
        self.check_comparator(registry)

    def test_core(self):

        def add_in_registry():

            @register(Core)
            class Base:

                @Declarations.classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test:
                pass

            @register(Model)
            class Test2:

                pass

        registry = self.init_registry(add_in_registry)
        self.check_comparator(registry)