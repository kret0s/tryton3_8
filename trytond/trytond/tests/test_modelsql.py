# -*- coding: utf-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.

import unittest
import time

from trytond import backend
from trytond.exceptions import UserError, ConcurrencyException
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.tests.test_tryton import install_module, with_transaction


class ModelSQLTestCase(unittest.TestCase):
    'Test ModelSQL'

    @classmethod
    def setUpClass(cls):
        install_module('tests')

    @unittest.skipIf(backend.name() == 'sqlite',
        'SQLite not concerned because tryton don\'t set "NOT NULL"'
        'constraint: "ALTER TABLE" don\'t support NOT NULL constraint'
        'without default value')
    @with_transaction()
    def test_required_field_missing(self):
        'Test error message when a required field is missing'
        pool = Pool()
        Modelsql = pool.get('test.modelsql')
        transaction = Transaction()

        fields = {
            'desc': '',
            'integer': 0,
            }
        for key, value in fields.iteritems():
            try:
                Modelsql.create([{key: value}])
            except UserError, err:
                # message must not quote key
                msg = "'%s' not missing but quoted in error: '%s'" % (key,
                        err.message)
                self.assertTrue(key not in err.message, msg)
            else:
                self.fail('UserError should be caught')
            transaction.cursor.rollback()

    @with_transaction()
    def test_check_timestamp(self):
        'Test check timestamp'
        pool = Pool()
        ModelsqlTimestamp = pool.get('test.modelsql.timestamp')
        transaction = Transaction()
        # cursor must be committed between each changes otherwise NOW() returns
        # always the same timestamp.
        cursor = transaction.cursor
        record, = ModelsqlTimestamp.create([{}])
        cursor.commit()

        timestamp = ModelsqlTimestamp.read([record.id],
            ['_timestamp'])[0]['_timestamp']

        if backend.name() in ('sqlite', 'mysql'):
            # timestamp precision of sqlite is the second
            time.sleep(1)

        ModelsqlTimestamp.write([record], {})
        cursor.commit()

        transaction.timestamp[str(record)] = timestamp
        self.assertRaises(ConcurrencyException,
            ModelsqlTimestamp.write, [record], {})

        transaction.timestamp[str(record)] = timestamp
        self.assertRaises(ConcurrencyException,
            ModelsqlTimestamp.delete, [record])

        transaction.timestamp.pop(str(record), None)
        ModelsqlTimestamp.write([record], {})
        cursor.commit()
        ModelsqlTimestamp.delete([record])
        cursor.commit()


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ModelSQLTestCase)
