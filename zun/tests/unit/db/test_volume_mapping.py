#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg
from oslo_utils import uuidutils
import six

from zun.common import exception
import zun.conf
from zun.db import api as dbapi
from zun.tests.unit.db import base
from zun.tests.unit.db import utils

CONF = zun.conf.CONF


class DbVolumeMappingTestCase(base.DbTestCase):

    def setUp(self):
        cfg.CONF.set_override('db_type', 'sql')
        super(DbVolumeMappingTestCase, self).setUp()

    def test_create_volume_mapping(self):
        utils.create_test_volume_mapping(context=self.context)

    def test_create_volume_mapping_already_exists(self):
        utils.create_test_volume_mapping(context=self.context,
                                         uuid='123')
        with self.assertRaisesRegex(exception.VolumeMappingAlreadyExists,
                                    'A volume mapping with UUID 123.*'):
            utils.create_test_volume_mapping(context=self.context,
                                             uuid='123')

    def test_get_volume_mapping_by_uuid(self):
        volume_mapping = utils.create_test_volume_mapping(context=self.context)
        res = dbapi.get_volume_mapping_by_uuid(self.context,
                                               volume_mapping.uuid)
        self.assertEqual(volume_mapping.id, res.id)
        self.assertEqual(volume_mapping.uuid, res.uuid)

    def test_get_volume_mapping_that_does_not_exist(self):
        self.assertRaises(exception.VolumeMappingNotFound,
                          dbapi.get_volume_mapping_by_uuid,
                          self.context,
                          uuidutils.generate_uuid())

    def test_list_volume_mappings(self):
        uuids = []
        for i in range(1, 6):
            volume_mapping = utils.create_test_volume_mapping(
                uuid=uuidutils.generate_uuid(),
                context=self.context)
            uuids.append(six.text_type(volume_mapping['uuid']))
        res = dbapi.list_volume_mappings(self.context)
        res_uuids = [r.uuid for r in res]
        self.assertEqual(sorted(uuids), sorted(res_uuids))

    def test_list_volume_mappings_sorted(self):
        uuids = []
        for i in range(5):
            volume_mapping = utils.create_test_volume_mapping(
                uuid=uuidutils.generate_uuid(),
                context=self.context)
            uuids.append(six.text_type(volume_mapping.uuid))
        res = dbapi.list_volume_mappings(self.context, sort_key='uuid')
        res_uuids = [r.uuid for r in res]
        self.assertEqual(sorted(uuids), res_uuids)

        self.assertRaises(exception.InvalidParameterValue,
                          dbapi.list_volume_mappings,
                          self.context,
                          sort_key='foo')

    def test_list_volume_mappings_with_filters(self):
        volume_mapping1 = utils.create_test_volume_mapping(
            volume_provider='provider-one',
            uuid=uuidutils.generate_uuid(),
            context=self.context)
        volume_mapping2 = utils.create_test_volume_mapping(
            volume_provider='provider-two',
            uuid=uuidutils.generate_uuid(),
            context=self.context)

        res = dbapi.list_volume_mappings(
            self.context, filters={'volume_provider': 'provider-one'})
        self.assertEqual([volume_mapping1.id], [r.id for r in res])

        res = dbapi.list_volume_mappings(
            self.context, filters={'volume_provider': 'provider-two'})
        self.assertEqual([volume_mapping2.id], [r.id for r in res])

        res = dbapi.list_volume_mappings(
            self.context, filters={'volume_provider': 'bad-provider'})
        self.assertEqual([], [r.id for r in res])

        res = dbapi.list_volume_mappings(
            self.context,
            filters={'volume_provider': volume_mapping1.volume_provider})
        self.assertEqual([volume_mapping1.id], [r.id for r in res])

    def test_destroy_volume_mapping(self):
        volume_mapping = utils.create_test_volume_mapping(context=self.context)
        dbapi.destroy_volume_mapping(self.context, volume_mapping.id)
        self.assertRaises(exception.VolumeMappingNotFound,
                          dbapi.get_volume_mapping_by_uuid,
                          self.context, volume_mapping.uuid)

    def test_destroy_volume_mapping_by_uuid(self):
        volume_mapping = utils.create_test_volume_mapping(context=self.context)
        dbapi.destroy_volume_mapping(self.context, volume_mapping.uuid)
        self.assertRaises(exception.VolumeMappingNotFound,
                          dbapi.get_volume_mapping_by_uuid,
                          self.context, volume_mapping.uuid)

    def test_destroy_volume_mapping_that_does_not_exist(self):
        self.assertRaises(exception.VolumeMappingNotFound,
                          dbapi.destroy_volume_mapping, self.context,
                          uuidutils.generate_uuid())

    def test_update_volume_mapping(self):
        volume_mapping = utils.create_test_volume_mapping(context=self.context)
        old_conn_info = volume_mapping.connection_info
        new_conn_info = 'new-conn-info'
        self.assertNotEqual(old_conn_info, new_conn_info)

        res = dbapi.update_volume_mapping(self.context, volume_mapping.id,
                                          {'connection_info': new_conn_info})
        self.assertEqual(new_conn_info, res.connection_info)

    def test_update_volume_mapping_not_found(self):
        volume_mapping_uuid = uuidutils.generate_uuid()
        new_conn_info = 'new-conn-info'
        self.assertRaises(exception.VolumeMappingNotFound,
                          dbapi.update_volume_mapping, self.context,
                          volume_mapping_uuid,
                          {'connection_info': new_conn_info})

    def test_update_volume_mapping_uuid(self):
        volume_mapping = utils.create_test_volume_mapping(context=self.context)
        self.assertRaises(exception.InvalidParameterValue,
                          dbapi.update_volume_mapping, self.context,
                          volume_mapping.id, {'uuid': ''})
