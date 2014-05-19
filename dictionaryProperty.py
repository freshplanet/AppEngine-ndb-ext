'''
Copyright 2014 FreshPlanet (http://freshplanet.com | opensource@freshplanet.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from UserDict import DictMixin

from google.appengine.api import datastore_errors
from google.appengine.ext import ndb


class DictionaryProperty(ndb.StructuredProperty):
    """
    A property that stores pairs of (key, value).
    
    The key will act as a new sub-property on the entity.
    Key names share the same restrictions as property names.
    
    The value can be among (int, float, basestring, datetime).
    The value can also be a ndb.Model but it should only be composed of simple non-repeated properties for the type mentioned.
    (you can try other types & repeated, that may work but at your own risk - well, as for this whole property but even more :)
    
    Values can be of different types across keys.
    
    This property is indexable (and is indexed by default).
    Contrary to a repeated property, each value is indexed separately: you can only query for a value after specifying the key it is linked to.
    You can't directly query for keys, or filter values across several keys.
    Ex: BrandStats.query(BrandStats.numberOfClients['FR'] == 0)
    
    This property is not tailored to be used with composite indexes.
    If you wanted to, you would have to declare every keys that have to be indexed.
    Actually, one goal is to avoid using them:
        If you have "brandName", "countryCode" and "numberOfClients" and all you want to query is the top brand in the country,
        instead of indexing both "countryCode" and "numberOfClients", you can use DictionaryProperty to regroup "countryCode" and "numberOfClients".
        But doing so you won't be able to query by numberOfClients only (if you do no longer have a "numberOfClients" property indexed).
        So think twice if DictionaryProperty is the right way to go for your use case.
    
    Note that the value of DictionaryProperty you manipulate is not directly a dict but the _DictLikeModel.
    Most of dict interface is implemented thanks to DictMixin (only 'copy' should be missing).
    
    Usage:
    
        class BrandStats(ndb.Model):
            brandName = ndb.StringProperty()
            numberOfClients = DictionaryProperty()
        
        stats = BrandStats(numberOfClients={'US':4})
        stats.numberOfClients = {'US':7}
        
        numberUS = stats.numberOfClients['US']
        stats.numberOfClients['FR'] = 5
        if 'BE' in stats.numberOfClients:
            del stats.numberOfClients['BE']
            
        numberBE = stats.numberOfClients.get('BE', 0)
        total = 0
        for country in stats.numberOfClients:
            total += stats.numberOfClients[country]
        
        topUsBrand = BrandStats.query().order(-BrandStats.numberOfClients['US']).get()
        frBrandsWithNoClients = BrandStats.query(BrandStats.numberOfClients['FR'] == 0).fetch(10)
        
        # This will not match entities with an empty dict, only entities with 'None' as numberOfClients's value
        # This is the only filter available directly on DictionaryProperty
        undefinedStats = BrandStats.query(BrandStats.numberOfClients == None).fetch(10)
        
        export = stats.to_dict() # {"brandName": None, "numberOfClients": {"US": 7, "FR": 5}}
    """
    
    def __init__(self, name=None, indexed=True, **kwds):
        super(DictionaryProperty, self).__init__(_DictLikeModel, name=name, indexed=indexed, **kwds)
    
    def __getitem__(self, key):
        """
        Build a Property to filter on a specify key.
        
        Ex:
        BrandSales.query(BrandSales.numberOfClients['FR'] == 0).fetch(10)
        """
        _DictLikeModel._validateKey(key)
        # Using the public "name" is not working, see Guido's answer here:
        # http://stackoverflow.com/questions/13631884/ndb-querying-a-genericproperty-in-repeated-expando-structuredproperty
        prop = ndb.GenericProperty()
        prop._name = self._name + '.' + key
        return prop
        
    def _comparison(self, op, value):
        if op == '=' and value is None:
            return super(DictionaryProperty, self)._comparison(op, value)
        else:
            raise datastore_errors.BadFilterError('DictionaryProperty cannot be used directly as filter except with "== None"')


class _DictLikeModel(ndb.Expando, DictMixin):
    """
    Internal model used to implement DictionaryProperty.
    This is what you actually manipulate when dealing with a DictionaryProperty value.
    """
    @classmethod
    def _validateKey(cls, key):
        if not isinstance(key, basestring):
            raise ValueError("DictionaryProperty keys must be strings, got: %r" % key)
        if key.startswith('_'):
            raise ValueError("DictionaryProperty keys must not start with '_', got: %s" % key)
    
    def __getitem__(self, key):
        self._validateKey(key)
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError("%s not found on DictionaryProperty value" % key)
    
    def __setitem__(self, key, value):
        self._validateKey(key)
        setattr(self, key, value)

    def __delitem__(self, key):
        try:
            # delattr can raise "TypeError: Model properties must be Property instances; not None"
            # We don't want to raise this error, but we don't want to catch all TypeError either.
            # So we call __getitem__ first.
            self.__getitem__(key)
            delattr(self, key)
        except AttributeError:
            raise KeyError("%s not found on DictionaryProperty value" % key)
        
    def __contains__(self, key):
        return key in self._properties
    
    def __iter__(self):
        return self._properties.iterkeys()

    def iteritems(self):
        """ @rtype: iter """
        for key in self._properties.iterkeys():
            yield (key, getattr(self, key))

    def keys(self):
        """ @rtype: list """
        return self._properties.keys()
