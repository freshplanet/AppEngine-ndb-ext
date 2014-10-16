# -*- coding: utf-8 -*-
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
import json

from google.appengine.ext import ndb


class JsonProperty(ndb.BlobProperty):
    """
    A property whose value is any Json-encodable Python object.
    
    We are improving the NDB one by having a more compact serialization
    (no spaces after , and :)
    
    Compatible with existing ndb.JsonProperty. Only for Python 2.7+
    """
    def _to_base_type(self, value):
        return json.dumps(value, separators=',:')
    
    def _from_base_type(self, value):
        return json.loads(value)
