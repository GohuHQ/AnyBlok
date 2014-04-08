# -*- coding: utf-8 -*-
from .anybloktestcase import AnyBlokTestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
import AnyBlok


class AnyBlokFieldTestCase(AnyBlokTestCase):
    """ Test case for all the Field, Column, RelationShip

    ::

        from anyblok.tests.anyblokfieldtestcase import AnyBlokFieldTestCase


        class TestMyField(AnyBlokFieldTestCase):

            ...

    .. warning::

        The database are create and drop for each unit test

    """

    part_to_load = ['AnyBlok']
    """ blok group to load """
    current_blok = 'anyblok-core'
    """ In the blok to add the new model """

    @classmethod
    def setUpClass(cls):
        """ Intialialise the argsparse manager """
        super(AnyBlokFieldTestCase, cls).setUpClass()
        cls.init_argsparse_manager()

    def setUp(self):
        """ Create a database and load the blok manager """
        super(AnyBlokFieldTestCase, self).setUp()
        self.createdb()
        BlokManager.load(*self.part_to_load)

    def tearDown(self):
        """ Clear the registry, unload the blok manager and  drop the database
        """
        RegistryManager.clear()
        BlokManager.unload()
        self.dropdb()
        super(AnyBlokFieldTestCase, self).tearDown()

    def init_registry(self, function, **kwargs):
        """ call a function to filled the blok manager with new model

        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        AnyBlok.current_blok = self.current_blok
        try:
            function(**kwargs)
        finally:
            AnyBlok.current_blok = None
        return self.getRegistry()