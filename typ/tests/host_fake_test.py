# Copyright 2014 Dirk Pranke. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import unittest

from typ.tests import host_test
from typ.host_fake import FakeHost


class TestFakeHost(host_test.TestHost):
    def host(self):
        return FakeHost()

    def test_for_mp(self):
        h = self.host()
        self.assertNotEqual(h.for_mp(), None)
