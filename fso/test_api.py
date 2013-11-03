# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/10/20
# copy: (C) CopyLoose 2009 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import sys, os, unittest, tempfile, uuid, stat

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


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
