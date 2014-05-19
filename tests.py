# -*- coding: utf-8 -*-
'''
Created on 29 nov. 2012

@author: Alexis
'''
import datetime
import os
import unittest

from google.appengine.api import datastore_errors
from google.appengine.ext import ndb, testbed

from dictionaryProperty import DictionaryProperty


class _BrandStats(ndb.Model):
    
    brandName = ndb.StringProperty()
    clients = DictionaryProperty()


class DictionaryPropertyTest(unittest.TestCase):
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        yamlPath = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
        self.testbed.init_datastore_v3_stub(auto_id_policy=testbed.AUTO_ID_POLICY_SCATTERED, require_indexes=True, root_path=yamlPath)
        self.testbed.init_memcache_stub()
        
    def tearDown(self):
        # restore the original stubs so that tests do not interfere with each other.
        self.testbed.deactivate()

    def testIt(self):
        
        stats = _BrandStats()
        stats.brandName = "Google"
        stats.clients = {"US": 7810}
        stats.put()
        
        result = _BrandStats.query(_BrandStats.clients['US'] == 7810).get()
        self.assertEqual(result, stats)
        stats = result
        
        stats.clients['FR'] = 78
        try:
            stats.clients['BE']
            self.fail("Should have raised KeyError")
        except KeyError:
            pass
        
        try:
            del stats.clients['BE']
            self.fail("Should have raised KeyError")
        except KeyError:
            pass
        
        del stats.clients['US']
        
        stats.put()
        
        result = _BrandStats.query(_BrandStats.clients['US'] == 7810).get()
        self.assertIsNone(result)
        
        result = _BrandStats.query(_BrandStats.clients['BE'] == 7810).get()
        self.assertIsNone(result)
        
        result = _BrandStats.query(_BrandStats.clients['FR'] < 7810).get()
        self.assertEqual(result, stats)
        
        # Test: filter for None
        stats = _BrandStats()
        stats.put()
        result = _BrandStats.query(_BrandStats.clients == None).get()
        self.assertEqual(result, stats)
        
        # Test: other comparisons
        try:
            _BrandStats.query(_BrandStats.clients < 7810).get()
            self.fail("Should raise an error")
        except datastore_errors.BadFilterError:
            pass
        
        # Test: define dict from constructor
        stats = _BrandStats(clients={"FR": 7})
        self.assertEqual(stats.clients['FR'], 7)
        
        # Test: IN
        self.assertTrue('FR' in stats.clients)
        
        # Test: to_dict()
        data = stats.to_dict()
        self.assertEqual(data['clients'], {"FR": 7})
        
        # Test: get()
        self.assertEqual(stats.clients.get('FR'), 7)
        self.assertEqual(stats.clients.get('ZZ', 0), 0)
        
        # Test: iter()
        stats.clients = {"FR": 5, "BE": 1}
        self.assertSetEqual({'FR', 'BE'}, {c for c in stats.clients})
        
        # Test: items():
        stats.put()
        stats = stats.key.get()
        items = list(stats.clients.iteritems())
        keys = {item[0] for item in items}
        self.assertSetEqual({'FR', 'BE'}, keys)
        for k, v in items:
            self.assertIsInstance(v, int)  # no GenericProperty
            self.assertEqual(v, stats.clients[k])
            
        # Test using datetime - simple GET
        now = datetime.datetime.utcnow()
        stats.clients = {'FR': now}
        stats.put()
        stats = stats.key.get()
        self.assertEqual(stats.clients.get('FR'), now)
        
        # Test empty check
        stats = _BrandStats(clients={})
        self.assertFalse(stats.clients)

# TODO: have GAE team fix this issue!
# https://code.google.com/p/googleappengine/issues/detail?id=10167
#         # Test using datetime - projection
#         stats = _BrandStats.query(_BrandStats.clients['FR'] >= now).get(projection=[_BrandStats.clients['FR']])
#         self.assertIsNotNone(stats)
#         self.assertEqual(stats.clients.get('FR'), now)
