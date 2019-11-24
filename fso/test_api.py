# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/10/20
# copy: (C) Copyright 2013-EOT metagriffin -- see LICENSE.txt
#------------------------------------------------------------------------------
# This software is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#------------------------------------------------------------------------------

import sys
import os
import unittest
import tempfile
import uuid
import stat

from . import api

#------------------------------------------------------------------------------
class TestApi(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_api_push(self):
    fname = tempfile.mktemp(prefix='fso-test_api-unittest.')
    tdata = 'random-unique-data:' + str(uuid.uuid4())
    self.assertFalse(os.path.exists(fname))
    with api.push() as overlay:
      self.assertFalse(os.path.exists(fname))
      with open(fname, 'wb') as fp:
        fp.write(tdata)
      self.assertTrue(os.path.exists(fname))
      self.assertEqual(len(overlay.entries), 1)
      entry = overlay.entries.values()[0]
      self.assertEqual(entry.path, fname)
      self.assertEqual(entry.mode, stat.S_IFREG)
      self.assertEqual(entry.content, tdata)
    self.assertFalse(os.path.exists(fname))

  #----------------------------------------------------------------------------
  def test_api_multipush(self):
    fname1 = tempfile.mktemp(prefix='fso-test_api-unittest.1.')
    fname2 = tempfile.mktemp(prefix='fso-test_api-unittest.2.')
    tdata1 = 'random-unique-data.1:' + str(uuid.uuid4())
    tdata2 = 'random-unique-data.2:' + str(uuid.uuid4())
    self.assertFalse(os.path.exists(fname1))
    self.assertFalse(os.path.exists(fname2))
    with api.push() as overlay1:
      self.assertFalse(os.path.exists(fname1))
      self.assertFalse(os.path.exists(fname2))
      with open(fname1, 'wb') as fp:
        fp.write(tdata1)
      self.assertTrue(os.path.exists(fname1))
      self.assertFalse(os.path.exists(fname2))
      with api.push() as overlay2:
        self.assertTrue(os.path.exists(fname1))
        self.assertFalse(os.path.exists(fname2))
        with open(fname2, 'wb') as fp:
          fp.write(tdata2)
        self.assertTrue(os.path.exists(fname1))
        self.assertTrue(os.path.exists(fname2))
        self.assertEqual(overlay1.entries.keys(), [fname1])
        self.assertEqual(overlay2.entries.keys(), [fname2])
      self.assertTrue(os.path.exists(fname1))
      self.assertFalse(os.path.exists(fname2))
    self.assertFalse(os.path.exists(fname1))
    self.assertFalse(os.path.exists(fname2))

  #----------------------------------------------------------------------------
  def test_api_apply(self):
    fname1 = tempfile.mktemp(prefix='fso-test_api-unittest.1.')
    self.assertFalse(os.path.exists(fname1))
    with api.push() as overlay:
      self.assertFalse(os.path.exists(fname1))
      overlay.apply({ fname1 : 'stuffs' })
      self.assertTrue(os.path.exists(fname1))
      with open(fname1, 'rb') as fp:
        self.assertEqual(fp.read(), 'stuffs')
    self.assertFalse(os.path.exists(fname1))


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
