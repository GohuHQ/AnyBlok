# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pkg_resources import iter_entry_points
from anyblok.imp import ImportManager
from .logging import log
from anyblok.environment import EnvironmentManager
from time import sleep
from sys import modules
from os.path import dirname
from logging import getLogger
from os.path import join

logger = getLogger(__name__)


class BlokManagerException(LookupError):
    """ Simple exception to BlokManager """

    def __init__(self, *args, **kwargs):
        EnvironmentManager.set('current_blok', None)
        super(BlokManagerException, self).__init__(*args, **kwargs)


class BlokManager:
    """ Manage the bloks for one process

    A blok has a `setuptools` entrypoint, this entry point is defined
    by the ``entry_points`` attribute in the first load

    The ``bloks`` attribute is a dict with all the loaded entry points

    Use this class to import all the bloks in the entrypoint::

        BlokManager.load()

    """

    bloks = {}
    entry_points = None
    ordered_bloks = []
    auto_install = []
    importers = {}

    @classmethod
    def list(cls):
        """ Return the ordered bloks

        :rtype: list of blok name ordered by loading
        """
        return cls.ordered_bloks

    @classmethod
    def has(cls, blok):
        """ Return True if the blok is loaded

        :param blok: blok name
        :rtype: bool
        """
        return blok and blok in cls.ordered_bloks or False

    @classmethod
    def get(cls, blok):
        """ Return the loaded blok

        :param blok: blok name
        :rtype: blok instance
        :exception: BlokManagerException
        """
        if not cls.has(blok):
            raise BlokManagerException('%r not found' % blok)

        return cls.bloks[blok]

    @classmethod
    def set(cls, blokname, blok):
        """ Add a new blok

        :param blokname: blok name
        :param blok: blok instance
        :exception: BlokManagerException
        """
        if cls.has(blokname):
            raise BlokManagerException('%r already present' % blokname)

        cls.bloks[blokname] = blok
        cls.ordered_bloks.append(blokname)

    @classmethod
    @log(logger)
    def reload(cls):
        """ Reload the entry points

        Empty the ``bloks`` dict and use the ``entry_points`` attribute to
        load bloks
        :exception: BlokManagerException
        """
        if cls.entry_points is None:
            raise BlokManagerException(
                """You must use the ``load`` classmethod before using """
                """``reload``""")

        entry_points = []
        entry_points += cls.entry_points
        cls.unload()
        cls.load(entry_points=entry_points)

    @classmethod
    @log(logger)
    def unload(cls):
        """ Unload all the bloks but not the registry """
        cls.bloks = {}
        cls.ordered_bloks = []
        cls.entry_points = None
        cls.auto_install = []
        from .registry import RegistryManager
        RegistryManager.unload()

    @classmethod
    def get_need_blok(cls, blok):
        if cls.has(blok):
            return True

        if blok not in cls.bloks:
            return False

        for required in cls.bloks[blok].required:
            if not cls.get_need_blok(required):
                raise BlokManagerException(
                    "Not %s required bloks found" % required)

            cls.bloks[required].required_by.append(blok)

        for optional in cls.bloks[blok].optional:
            if cls.get_need_blok(optional):
                cls.bloks[optional].optional_by.append(blok)

        for conditional in cls.bloks[blok].conditional:
            cls.bloks[conditional].conditional_by.append(blok)

        for conflicting in cls.bloks[blok].conflicting:
            cls.bloks[conflicting].conflicting_by.append(blok)

        cls.ordered_bloks.append(blok)
        EnvironmentManager.set('current_blok', blok)

        if not ImportManager.has(blok):
            # Import only if not exist don't reload here
            mod = ImportManager.add(blok)
            mod.imports()
        else:
            mod = ImportManager.get(blok)
            mod.reload()

        if cls.bloks[blok].autoinstall:
            cls.auto_install.append(blok)

        return True

    @classmethod
    @log(logger)
    def load(cls, entry_points=('bloks',)):
        """ Load all the bloks and import them

        :param entry_points: Use by ``iter_entry_points`` to get the blok
        :exception: BlokManagerException
        """
        if not entry_points:
            raise BlokManagerException("The entry_points mustn't be empty")

        cls.entry_points = entry_points

        if EnvironmentManager.get('current_blok'):
            while EnvironmentManager.get('current_blok'):
                sleep(0.1)

        EnvironmentManager.set('current_blok', 'start')

        bloks = []
        for entry_point in entry_points:
            count = 0
            for i in iter_entry_points(entry_point):
                count += 1
                blok = i.load()
                blok.required_by = []
                blok.optional_by = []
                blok.conditional_by = []
                blok.conflicting_by = []
                cls.set(i.name, blok)
                blok.name = i.name
                bloks.append((blok.priority, i.name))

            if not count:
                raise BlokManagerException(
                    "Invalid bloks group %r" % entry_point)

        # Empty the ordered blok to reload it depending on the priority
        cls.ordered_bloks = []
        bloks.sort()

        try:
            while bloks:
                blok = bloks.pop(0)[1]
                cls.get_need_blok(blok)

        finally:
            EnvironmentManager.set('current_blok', None)

    @classmethod
    def getPath(cls, blok):
        """ Return the path of the blok

        :param blok: blok name in ``ordered_bloks``
        :rtype: absolute path
        """
        blok = cls.get(blok)
        return dirname(modules[blok.__module__].__file__)

    @classmethod
    def add_importer(cls, key, cls_name):
        """ Add a new importer

        :param key: key of the importer
        :param cls_name: name of the model to import
        """
        cls.importers[key] = cls_name

    @classmethod
    def has_importer(cls, key):
        """ Check if an importer  """
        return True if key in cls.importers else False

    @classmethod
    def get_importer(cls, key):
        """ Get the importer class name

        :param key: key of the importer
        :rtype: name of the model to import
        :exception: BlokManagerException
        """
        if not cls.has_importer(key):
            raise BlokManagerException(
                "No importer found for the key %r" % key)

        return cls.importers[key]


class Blok:
    """ Super class for all the bloks

    define the default value for:

    * priority: order to load the blok
    * required: list of the bloks needed to install this blok
    * optional: list of the bloks to be installed if present in the blok list
    * conditional: if all the bloks of this list are installed then install
      this blok
    """

    autoinstall = False
    priority = 100
    required = []
    optional = []
    conditional = []
    conflicting = []
    name = None  # filled by the BlokManager

    def __init__(self, registry):
        self.registry = registry

    @classmethod
    def import_declaration_module(cls):
        """ Do the python import for the Declaration of the model or other
        """

    def update(self, latest_version):
        """ Call at the installation or update

        :param latest_version: latest version installed, if the blok have not
                               been installing the latest_version will be None
        """

    def pre_migration(self, latest_version):
        """Call at update, before the automigration

        .. warning::

            You can not use the ORM

        :param latest_version: latest version installed, if the blok have not
                               been installing the latest_version will be None
        """

    def post_migration(self, latest_version):
        """Call at update, after the automigration

        :param latest_version: latest version installed, if the blok have not
                               been installing the latest_version will be None
        """

    def uninstall(self):
        """ Call at the uninstallation
        """

    def load(self):
        """ Call at the launch of the application
        """

    def import_file(self, importer_name, model, *file_path, **kwargs):
        """ Import data file

        :param importer_name: Name of the importer (need installation of the
                              Blok which have the importer)
        :param model: Model of the data to import
        :param \*file_path: relative path of the path in this Blok
        :param \*\*kwargs: Option for the importer
        :rtype: return dict of result
        """
        blok_path = BlokManager.getPath(self.name)
        _file = join(blok_path, *file_path)
        logger.info("import %r file: %r", importer_name, _file)
        Importer = self.registry.get(BlokManager.get_importer(importer_name))
        file_to_import = None
        with open(_file, 'rb') as fp:
            file_to_import = fp.read()

        importer = Importer.insert(
            model=model, file_to_import=file_to_import, **kwargs)
        res = importer.run()
        logger.info("Create %d entries, Update %d entries",
                    len(res['created_entries']), len(res['updated_entries']))
        if res['error_found']:
            for error in res['error_found']:
                logger.error(error)
        else:
            importer.delete()

        return res
