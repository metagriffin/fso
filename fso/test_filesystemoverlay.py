# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2009/09/11
# copy: (C) CopyLoose 2009 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import sys, os, unittest, tempfile

from .filesystemoverlay import FileSystemOverlay

#------------------------------------------------------------------------------
class TestFileSystemOverlay(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_overlay_create(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fso.install()
    fp = open(fname, 'wb')
    fp.write('temporary filename: ')
    fp.write(fname)
    fp.close()
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fso.uninstall()
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlay_append(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fso.install()
    fp = open(fname, 'wb')
    fp.write('temporary filename: ')
    fp.write(fname)
    fp.close()
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fp = open(fname, 'ab')
    fp.write(' (that is all, folks)')
    fp.close()
    self.assertEqual(
      open(fname, 'rb').read(),
      'temporary filename: ' + fname + ' (that is all, folks)')
    fso.uninstall()
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlay_appendToReal(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fp = open(fname, 'wb')
    fp.write('temporary filename: ')
    fp.write(fname)
    fp.close()
    self.assertTrue(os.path.exists(fname), 'temporary file could not be created')
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fso.install()
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fp = open(fname, 'ab')
    fp.write(' (that is all, folks)')
    fp.close()
    self.assertEqual(
      open(fname, 'rb').read(),
      'temporary filename: ' + fname + ' (that is all, folks)')
    fso.uninstall()
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    os.unlink(fname)
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlay_deleteReal(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fp = open(fname, 'wb')
    fp.write('temporary filename: ')
    fp.write(fname)
    fp.close()
    self.assertTrue(os.path.exists(fname), 'temporary file could not be created')
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fso.install()
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    os.unlink(fname)
    self.assertFalse(os.path.exists(fname), 'temporary file delete failed')
    fso.uninstall()
    self.assertTrue(os.path.exists(fname), 'delete-through occurred')
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    os.unlink(fname)
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlay_contextmanager(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    with FileSystemOverlay(install=False) as fso:
      self.assertFalse(os.path.exists(fname), 'temporary file appeared prematurely')
      with open(fname, 'wb') as fp:
        fp.write('temporary filename: ')
        fp.write(fname)
      self.assertTrue(os.path.exists(fname), 'temporary file did not incarnate')
      with open(fname, 'rb') as fp:
        self.assertEqual(fp.read(), 'temporary filename: ' + fname)
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlayentry_contextmanager_read(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    with open(fname, 'wb') as fp:
      fp.write('temporary filename: ')
      fp.write(fname)
    self.assertTrue(os.path.exists(fname), 'temporary file could not be created')
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fso.install()
    with open(fname, 'rb') as fp:
      self.assertEqual(fp.read(), 'temporary filename: ' + fname)
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fp = open(fname, 'ab')
    fp.write(' (that is all, folks)')
    fp.close()
    with open(fname, 'rb') as fp:
      self.assertEqual(fp.read(), 'temporary filename: ' + fname + ' (that is all, folks)')
    self.assertEqual(
      open(fname, 'rb').read(),
      'temporary filename: ' + fname + ' (that is all, folks)')
    fso.uninstall()
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    os.unlink(fname)
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlayentry_contextmanager_write(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fso.install()
    with open(fname, 'wb') as fp:
      fp.write('temporary filename: ')
      fp.write(fname)
    self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    fso.uninstall()
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_overlay_multipleInstallsAndUninstalls(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(fso.installed or fso.active)
    fso.install()
    self.assertTrue(fso.installed and fso.active)
    fso.install()
    self.assertTrue(fso.installed and fso.active)
    with fso as overlay:
      self.assertTrue(fso.installed and fso.active)
      with open(fname, 'wb') as fp:
        fp.write('temporary filename: ')
        fp.write(fname)
      self.assertEqual(len(overlay.entries), 1)
      self.assertTrue(fso.installed and fso.active)
    self.assertFalse(fso.installed or fso.active)
    self.assertEqual(len(overlay.entries), 0)
    fso.uninstall()
    self.assertFalse(fso.installed or fso.active)

  #----------------------------------------------------------------------------
  def test_overlay_uninstallEntries(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.')
    fso = FileSystemOverlay(install=False)
    fso.install()
    self.assertFalse(os.path.exists(fname))
    with open(fname, 'wb') as fp:
      fp.write('temporary filename: ')
      fp.write(fname)
    self.assertTrue(os.path.exists(fname))
    entries = fso.uninstall()
    self.assertFalse(os.path.exists(fname))
    self.assertEqual(entries.keys(), [fname])
    entry = entries[fname]
    self.assertEqual(entry.path, fname)
    self.assertEqual(entry.type, 'file')
    self.assertEqual(entry.content, 'temporary filename: ' + fname)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
