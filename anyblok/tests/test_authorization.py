# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .testcase import DBTestCase
from ..blok import BlokManager
from anyblok.test_bloks.authorization import TestPolicyOne
from anyblok.test_bloks.authorization import TestPolicyTwo
from anyblok.authorization import deny_all


class TestAuthorizationDeclaration(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def tearDown(self):
        super(TestAuthorizationDeclaration, self).tearDown()
        BlokManager.unload()

    def test_association(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok8',))
        record = registry.Test(id=23, label='Hop')
        self.assertIsInstance(registry.lookup_policy(record, 'Read'),
                              TestPolicyOne)
        self.assertIsInstance(registry.lookup_policy(record, 'Other'),
                              TestPolicyTwo)

        record = registry.Test2(id=2, label='Hop')
        self.assertIs(registry.lookup_policy(record, 'Read'), deny_all)
