# -*- coding: utf-8 -*-
import unittest
from anyblok.blok import BlokManager, BlokManagerException


class TestBlokManager(unittest.TestCase):

    def tearDown(self):
        super(TestBlokManager, self).tearDown()
        BlokManager.unload()
        BlokManager.bloks_groups = None

    def test_load_anyblok(self):
        BlokManager.load('AnyBlok')
        if not BlokManager.list():
            self.fail('No blok load')
        if not BlokManager.has('anyblok-core'):
            self.fail("The blok 'anyblok-core' is missing")

        BlokManager.get('anyblok-core')

    def test_load_with_invalid_blok_group(self):
        try:
            BlokManager.load('Invalid blok group')
            self.fail('Load with invalid blok group')
        except BlokManagerException:
            pass

    def test_reload(self):
        BlokManager.load('AnyBlok')
        BlokManager.set('invalid blok', None)
        BlokManager.get('invalid blok')
        BlokManager.reload()
        try:
            BlokManager.get('invalid blok')
            self.fail("Reload classmethod doesn't reload the bloks")
        except BlokManagerException:
            pass

    def test_reload_without_load(self):
        try:
            BlokManager.reload()
            self.fail('No exception when reload without previously load')
        except BlokManagerException:
            pass

    def test_get_invalid_blok(self):
        try:
            BlokManager.load('AnyBlok')
            BlokManager.get('invalid blok')
            self.fail('No exception when get invalid blok')
        except BlokManagerException:
            pass

    def test_get_files_from(self):
        BlokManager.load('AnyBlok')
        BlokManager.get_files_from('anyblok-core', 'imports')