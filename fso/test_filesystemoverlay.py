# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2009/09/11
# copy: (C) Copyright 2009-EOT metagriffin -- see LICENSE.txt
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

# IMPORTANT NOTE: in these routines, i am purposefully not doing a
# shutil.rmtree() when doing a `os.rmdir()` so that the presence of
# any unexpected files will cause an exception.

import sys, os, unittest, tempfile, stat, shutil, uuid

from .filesystemoverlay import FileSystemOverlay

#------------------------------------------------------------------------------
class TestFileSystemOverlay(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def test_links(self):
    tfiles = [
      os.path.join('link'),
      os.path.join('slink'),
      os.path.join('flink'),
      os.path.join('reallink'),
      os.path.join('deadlink'),
      os.path.join('file'),
      os.path.join('dir'),
      os.path.join('dir', 'file'),
      os.path.join('dir', 'subdir'),
      os.path.join('dir', 'subdir', 'file'),
      ]
    tdir = tempfile.mkdtemp(prefix='fso-test_filesystemoverlay-unittest.links.')
    for tfile in tfiles:
      self.assertFalse(os.path.exists(os.path.join(tdir, tfile)))
    self.assertEqual(os.listdir(tdir), [])
    fso = FileSystemOverlay(install=False)
    for tfile in tfiles:
      self.assertFalse(os.path.exists(os.path.join(tdir, tfile)))
      self.assertFalse(os.path.lexists(os.path.join(tdir, tfile)))
    self.assertEqual(os.listdir(tdir), [])
    os.symlink('dir/subdir/file', os.path.join(tdir, 'reallink'))
    with fso.install() as fso:
      for tfile in tfiles:
        self.assertFalse(os.path.exists(os.path.join(tdir, tfile)))
        if not tfile == 'reallink':
          self.assertFalse(os.path.lexists(os.path.join(tdir, tfile)))
      self.assertTrue(os.path.lexists(os.path.join(tdir, 'reallink')))
      self.assertEqual(os.listdir(tdir), ['reallink'])
      os.symlink('no-such-file', os.path.join(tdir, 'deadlink'))
      os.symlink('dir', os.path.join(tdir, 'link'))
      os.symlink('dir/subdir', os.path.join(tdir, 'slink'))
      os.symlink('dir/subdir/file', os.path.join(tdir, 'flink'))
      for tfile in tfiles:
        if tfile.endswith('link'):
          self.assertTrue(os.path.lexists(os.path.join(tdir, tfile)),
                          'expected link "%s" to exist' % (tfile,))
      self.assertEqual(sorted(os.listdir(tdir)), ['deadlink', 'flink', 'link', 'reallink', 'slink'])
      fso_changes = [
        'add:' + os.path.join(tdir, 'deadlink'),
        'add:' + os.path.join(tdir, 'flink'),
        'add:' + os.path.join(tdir, 'link'),
        'add:' + os.path.join(tdir, 'slink'),
        ]
      self.assertEqual(fso.changes, fso_changes)
      with FileSystemOverlay() as fso2:
        self.assertEqual(fso2.changes, [])
        self.assertEqual(os.readlink(os.path.join(tdir, 'link')), 'dir')
        self.assertEqual(sorted(os.listdir(tdir)), ['deadlink', 'flink', 'link', 'reallink', 'slink'])
        os.unlink(os.path.join(tdir, 'link'))
        self.assertEqual(fso2.changes, ['del:' + os.path.join(tdir, 'link')])
        self.assertEqual(sorted(os.listdir(tdir)), ['deadlink', 'flink', 'reallink', 'slink'])
        self.assertEqual(fso.changes, fso_changes)
        with self.assertRaises(OSError):
          os.readlink(os.path.join(tdir, 'link'))
      self.assertEqual(fso.changes, fso_changes)
      self.assertEqual(os.readlink(os.path.join(tdir, 'link')), 'dir')
    for tfile in tfiles:
      self.assertFalse(os.path.exists(os.path.join(tdir, tfile)))
      if not tfile == 'reallink':
        self.assertFalse(os.path.lexists(os.path.join(tdir, tfile)))
    self.assertTrue(os.path.lexists(os.path.join(tdir, 'reallink')))
    self.assertEqual(os.listdir(tdir), ['reallink'])
    os.unlink(os.path.join(tdir, 'reallink'))
    for tfile in tfiles:
      self.assertFalse(os.path.exists(os.path.join(tdir, tfile)))
    self.assertEqual(os.listdir(tdir), [])
    os.rmdir(tdir)

  #----------------------------------------------------------------------------
  def test_dirs(self):
    tdir = tempfile.mkdtemp(prefix='fso-test_filesystemoverlay-unittest.dirs.')
    self.assertEqual(os.listdir(tdir), [])
    with self.assertRaises(OSError):
      os.mkdir(os.path.join(tdir, 'a/b/c/d'))
    os.makedirs(os.path.join(tdir, 'a','b','c'))
    with self.assertRaises(OSError):
      os.makedirs(os.path.join(tdir, 'a','b','c'))
    os.mkdir(os.path.join(tdir, 'a/b/c/d'))
    os.symlink('foo',os.path.join(tdir, 'a/b/c/d/bar'))
    no_fso_walk = [
      (tdir, ['a'], []),
      (os.path.join(tdir, 'a'), ['b'], []),
      (os.path.join(tdir, 'a/b'), ['c'], []),
      (os.path.join(tdir, 'a/b/c'), ['d'], []),
      (os.path.join(tdir, 'a/b/c/d'), [], ['bar']),
      ]
    self.assertEqual(list(os.walk(tdir)), no_fso_walk)
    with FileSystemOverlay() as fso:
      self.assertEqual(list(os.walk(tdir)), no_fso_walk)
      with self.assertRaises(OSError):
        os.mkdir(os.path.join(tdir, 's/t/u/v'))
      os.makedirs(os.path.join(tdir, 's','t','u'))
      with self.assertRaises(OSError):
        os.makedirs(os.path.join(tdir, 's','t','u'))
      self.assertEqual(
        list(os.walk(tdir)),
        [(tdir, ['a', 's'], [])] +
        no_fso_walk[1:] +
        [
          (os.path.join(tdir, 's'), ['t'], []),
          (os.path.join(tdir, 's/t'), ['u'], []),
          (os.path.join(tdir, 's/t/u'), [], []),
          ])
      os.mkdir(os.path.join(tdir, 's/t/u/v'))
      os.symlink('zog',os.path.join(tdir, 's/t/u/v/zig'))
      self.assertEqual(
        list(os.walk(tdir)),
        [(tdir, ['a', 's'], [])] +
        no_fso_walk[1:] +
        [
          (os.path.join(tdir, 's'), ['t'], []),
          (os.path.join(tdir, 's/t'), ['u'], []),
          (os.path.join(tdir, 's/t/u'), ['v'], []),
          (os.path.join(tdir, 's/t/u/v'), [], ['zig']),
          ])
      os.unlink(os.path.join(tdir, 's/t/u/v/zig'))
      os.rmdir(os.path.join(tdir, 's/t/u/v'))
      os.rmdir(os.path.join(tdir, 's/t/u'))
      os.rmdir(os.path.join(tdir, 's/t'))
      os.rmdir(os.path.join(tdir, 's'))
      self.assertEqual(list(os.walk(tdir)), no_fso_walk)
      self.assertEqual(fso.changes, [])
      os.unlink(os.path.join(tdir, 'a/b/c/d/bar'))
      self.assertEqual(fso.changes, ['del:' + os.path.join(tdir, 'a/b/c/d/bar')])
    self.assertEqual(list(os.walk(tdir)), no_fso_walk)
    os.unlink(os.path.join(tdir, 'a/b/c/d/bar'))
    os.rmdir(os.path.join(tdir, 'a/b/c/d'))
    os.rmdir(os.path.join(tdir, 'a/b/c'))
    os.rmdir(os.path.join(tdir, 'a/b'))
    os.rmdir(os.path.join(tdir, 'a'))
    os.rmdir(tdir)

  #----------------------------------------------------------------------------
  def test_rmtree(self):
    tdir = tempfile.mkdtemp(prefix='fso-test_filesystemoverlay-unittest.rmtree.')
    self.assertEqual(os.listdir(tdir), [])
    os.makedirs(os.path.join(tdir, 'a/b/c/d'))
    os.symlink('foo', os.path.join(tdir, 'a/b/c/d/bar'))
    with open(os.path.join(tdir, 'a/b/c/file'), 'wb') as fp:
      fp.write('data')
    no_fso_walk = [
      (tdir, ['a'], []),
      (os.path.join(tdir, 'a'), ['b'], []),
      (os.path.join(tdir, 'a/b'), ['c'], []),
      (os.path.join(tdir, 'a/b/c'), ['d'], ['file']),
      (os.path.join(tdir, 'a/b/c/d'), [], ['bar']),
      ]
    self.assertEqual(list(os.walk(tdir)), no_fso_walk)
    with FileSystemOverlay() as fso:
      self.assertEqual(list(os.walk(tdir)), no_fso_walk)
      shutil.rmtree(os.path.join(tdir, 'a/b/c'))
      self.assertEqual(list(os.walk(tdir)), [
        (tdir, ['a'], []),
        (os.path.join(tdir, 'a'), ['b'], []),
        (os.path.join(tdir, 'a/b'), [], []),
        ])
      self.assertEqual(fso.changes, [
        'del:' + os.path.join(tdir, 'a/b/c'),
        'del:' + os.path.join(tdir, 'a/b/c/d'),
        'del:' + os.path.join(tdir, 'a/b/c/d/bar'),
        'del:' + os.path.join(tdir, 'a/b/c/file'),
        ])
    self.assertEqual(list(os.walk(tdir)), no_fso_walk)
    shutil.rmtree(os.path.join(tdir, 'a/b/c'))
    os.rmdir(os.path.join(tdir, 'a/b'))
    os.rmdir(os.path.join(tdir, 'a'))
    os.rmdir(tdir)

  #----------------------------------------------------------------------------
  def test_create(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.create.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    with fso as fso:
      fp = open(fname, 'wb')
      fp.write('temporary filename: ')
      fp.write(fname)
      fp.close()
      self.assertEqual('temporary filename: ' + fname, open(fname, 'rb').read())
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_access(self):
    tdir = tempfile.mkdtemp(prefix='fso-test_filesystemoverlay-unittest.access.')
    os.makedirs(os.path.join(tdir, 'a/b/c/d'))
    os.symlink('foo',os.path.join(tdir, 'a/b/c/d/bar'))
    with open(os.path.join(tdir, 'a/b/c/file'), 'wb') as fp:
      fp.write('data')
    self.assertTrue(os.access(os.path.join(tdir, 'a/b/c/file'), os.F_OK | os.R_OK | os.W_OK))
    self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/file'), os.X_OK))
    self.assertTrue(os.access(os.path.join(tdir, 'a/b/c/file'), os.W_OK))
    self.assertTrue(os.access(os.path.join(tdir, 'a/b/c/file'), os.R_OK))
    self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.F_OK))
    self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.X_OK))
    self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.W_OK))
    self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.R_OK))
    with FileSystemOverlay() as fso:
      self.assertTrue(os.access(os.path.join(tdir, 'a/b/c/file'), os.F_OK | os.R_OK | os.W_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/file'), os.X_OK))
      self.assertTrue(os.access(os.path.join(tdir, 'a/b/c/file'), os.W_OK))
      self.assertTrue(os.access(os.path.join(tdir, 'a/b/c/file'), os.R_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.F_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.X_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.W_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/b/c/notfile'), os.R_OK))
      os.mkdir(os.path.join(tdir, 'a/fso'))
      with open(os.path.join(tdir, 'a/fso/file'), 'wb') as fp:
        fp.write('fso.data')
      self.assertTrue(os.access(os.path.join(tdir, 'a/fso/file'), os.F_OK | os.R_OK | os.W_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/fso/file'), os.X_OK))
      self.assertTrue(os.access(os.path.join(tdir, 'a/fso/file'), os.W_OK))
      self.assertTrue(os.access(os.path.join(tdir, 'a/fso/file'), os.R_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/fso/notfile'), os.F_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/fso/notfile'), os.X_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/fso/notfile'), os.W_OK))
      self.assertFalse(os.access(os.path.join(tdir, 'a/fso/notfile'), os.R_OK))
    os.unlink(os.path.join(tdir, 'a/b/c/d/bar'))
    os.unlink(os.path.join(tdir, 'a/b/c/file'))
    os.rmdir(os.path.join(tdir, 'a/b/c/d'))
    os.rmdir(os.path.join(tdir, 'a/b/c'))
    os.rmdir(os.path.join(tdir, 'a/b'))
    os.rmdir(os.path.join(tdir, 'a'))
    os.rmdir(tdir)

  #----------------------------------------------------------------------------
  def test_append(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.append.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    with fso as fso:
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
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_appendToReal(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.appendtoreal.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fp = open(fname, 'wb')
    fp.write('temporary filename: ')
    fp.write(fname)
    fp.close()
    self.assertTrue(os.path.exists(fname), 'temporary file could not be created')
    self.assertEqual(open(fname, 'rb').read(), 'temporary filename: ' + fname)
    with fso as fso:
      self.assertEqual(open(fname, 'rb').read(), 'temporary filename: ' + fname)
      fp = open(fname, 'ab')
      fp.write(' (that is all, folks)')
      fp.close()
      self.assertEqual(
        open(fname, 'rb').read(),
        'temporary filename: ' + fname + ' (that is all, folks)')
    self.assertEqual(open(fname, 'rb').read(), 'temporary filename: ' + fname)
    os.unlink(fname)
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_deleteReal(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.deletereal.')
    fso = FileSystemOverlay(install=False)
    self.assertFalse(os.path.exists(fname), 'temporary file already existed')
    fp = open(fname, 'wb')
    fp.write('temporary filename: ')
    fp.write(fname)
    fp.close()
    self.assertTrue(os.path.exists(fname), 'temporary file could not be created')
    self.assertEqual(open(fname, 'rb').read(), 'temporary filename: ' + fname)
    with fso as fso:
      self.assertEqual(open(fname, 'rb').read(), 'temporary filename: ' + fname)
      os.unlink(fname)
      self.assertFalse(os.path.exists(fname), 'temporary file delete failed')
    self.assertTrue(os.path.exists(fname), 'delete-through occurred')
    self.assertEqual(open(fname, 'rb').read(), 'temporary filename: ' + fname)
    os.unlink(fname)
    self.assertFalse(os.path.exists(fname), 'write-through occurred')

  #----------------------------------------------------------------------------
  def test_contextmanager(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.contextmanager.')
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
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.contextmanager_read.')
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
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.contextmanager_write.')
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
  def test_multipleInstallsAndUninstalls(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.multipleinstallsanduninstalls.')
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
  def test_vaporized(self):
    fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.uninstallentries.')
    fso = FileSystemOverlay(install=False)
    self.assertIsNone(fso.vaporized)
    with fso as fso:
      self.assertFalse(os.path.exists(fname))
      with open(fname, 'wb') as fp:
        fp.write('temporary filename: ')
        fp.write(fname)
      self.assertTrue(os.path.exists(fname))
    entries = fso.vaporized
    self.assertFalse(os.path.exists(fname))
    self.assertEqual(entries.keys(), [fname])
    entry = entries[fname]
    self.assertEqual(entry.path, fname)
    self.assertEqual(entry.mode, stat.S_IFREG)
    self.assertEqual(entry.content, 'temporary filename: ' + fname)

  #----------------------------------------------------------------------------
  def test_changes(self):
    tdir = tempfile.mkdtemp(prefix='fso-test_filesystemoverlay-unittest.changes.')
    os.makedirs(os.path.join(tdir, 'a','b','c'))
    os.mkdir(os.path.join(tdir, 'a/b/c/d'))
    os.symlink('foo',os.path.join(tdir, 'a/b/c/d/bar'))
    os.symlink('file',os.path.join(tdir, 'a/b/link'))
    os.symlink('no-such-file',os.path.join(tdir, 'a/b/deadlink'))
    with open(os.path.join(tdir, 'a/b/zig'), 'wb') as fp:
      fp.write('zog')
    with open(os.path.join(tdir, 'a/b/file'), 'wb') as fp:
      fp.write('data')
    with FileSystemOverlay() as fso:
      os.unlink(os.path.join(tdir, 'a/b/c/d/bar'))
      os.rmdir(os.path.join(tdir, 'a/b/c/d'))
      os.rmdir(os.path.join(tdir, 'a/b/c'))
      with open(os.path.join(tdir, 'a/b/zig'), 'ab') as fp:
        fp.write('zug')
      with open(os.path.join(tdir, 'a/b/bling'), 'ab') as fp:
        fp.write('blang')
      with open(os.path.join(tdir, 'a/b/deadlink'), 'ab') as fp:
        fp.write('alive')
      with open(os.path.join(tdir, 'a/b/link'), 'ab') as fp:
        fp.write('then')
      self.assertEqual(fso.changes, [
        'add:' + os.path.join(tdir, 'a/b/bling'),
        'del:' + os.path.join(tdir, 'a/b/c'),
        'del:' + os.path.join(tdir, 'a/b/c/d'),
        'del:' + os.path.join(tdir, 'a/b/c/d/bar'),
        'mod:' + os.path.join(tdir, 'a/b/file'),
        'add:' + os.path.join(tdir, 'a/b/no-such-file'),
        'mod:' + os.path.join(tdir, 'a/b/zig'),
        ])
      self.assertEqual(fso.getChanges(tdir), [
        'add:a/b/bling',
        'del:a/b/c',
        'del:a/b/c/d',
        'del:a/b/c/d/bar',
        'mod:a/b/file',
        'add:a/b/no-such-file',
        'mod:a/b/zig',
        ])
      self.assertEqual(fso.getChanges(os.path.join(tdir, 'a/b/c')), [
        'del:',
        'del:d',
        'del:d/bar',
        ])
    chk = [
      (tdir, ['a'], []),
      (os.path.join(tdir, 'a'), ['b'], []),
      (os.path.join(tdir, 'a/b'), ['c'], ['deadlink', 'file', 'link', 'zig']),
      (os.path.join(tdir, 'a/b/c'), ['d'], []),
      (os.path.join(tdir, 'a/b/c/d'), [], ['bar']),
      ]
    out = [(w[0], sorted(w[1]), sorted(w[2])) for w in os.walk(tdir)]
    self.assertEqual(out, chk)
    self.assertEqual(open(os.path.join(tdir, 'a/b/zig'), 'rb').read(), 'zog')
    self.assertEqual(open(os.path.join(tdir, 'a/b/file'), 'rb').read(), 'data')
    self.assertEqual(os.readlink(os.path.join(tdir, 'a/b/c/d/bar')), 'foo')
    self.assertEqual(os.readlink(os.path.join(tdir, 'a/b/link')), 'file')
    self.assertEqual(os.readlink(os.path.join(tdir, 'a/b/deadlink')), 'no-such-file')
    os.unlink(os.path.join(tdir, 'a/b/c/d/bar'))
    os.unlink(os.path.join(tdir, 'a/b/link'))
    os.unlink(os.path.join(tdir, 'a/b/deadlink'))
    os.unlink(os.path.join(tdir, 'a/b/zig'))
    os.unlink(os.path.join(tdir, 'a/b/file'))
    os.rmdir(os.path.join(tdir, 'a/b/c/d'))
    os.rmdir(os.path.join(tdir, 'a/b/c'))
    os.rmdir(os.path.join(tdir, 'a/b'))
    os.rmdir(os.path.join(tdir, 'a'))
    os.rmdir(tdir)

  #----------------------------------------------------------------------------
  def test_tempfile_mktemp(self):
    with FileSystemOverlay() as fso:
      fname = tempfile.mktemp(prefix='fso-test_filesystemoverlay-unittest.mktemp.')
      with open(fname, 'wb') as fp:
        fp.write('fname: ' + fname + '\n')
    self.assertFalse(os.path.exists(fname))

  #----------------------------------------------------------------------------
  def test_tempfile_mkstemp(self):
    with FileSystemOverlay() as fso:
      fd, fname = tempfile.mkstemp(prefix='fso-test_filesystemoverlay-unittest.mkstemp.')
      with os.fdopen(fd, 'wb') as fp:
        fp.write('fname: ' + fname + '\n')
    self.assertFalse(os.path.exists(fname))

  #----------------------------------------------------------------------------
  def test_os_open(self):
    fname = '/tmp/fso-unittest.osopen-' + str(uuid.uuid4()) + '.tmp'
    with FileSystemOverlay() as fso:
      fd = os.open(fname, os.O_CREAT|os.O_WRONLY, 0644)
      os.write(fd, 'osopen.test\n')
      os.close(fd)
      with open(fname, 'rb') as fp:
        self.assertEqual(fp.read(), 'osopen.test\n')
      self.assertTrue(os.path.exists(fname))
    self.assertFalse(os.path.exists(fname))

  #----------------------------------------------------------------------------
  def test_passthru_mktemp(self):
    with FileSystemOverlay(passthru='.*fso-unittest\\.passthru\\.keep\\..*') as fso:
      fkeep = tempfile.mktemp(prefix='fso-unittest.passthru.keep.')
      fdrop = tempfile.mktemp(prefix='fso-unittest.passthru.drop.')
      with open(fkeep, 'wb') as fp:
        fp.write('keep')
      with open(fdrop, 'wb') as fp:
        fp.write('drop')
    self.assertFalse(os.path.exists(fdrop))
    self.assertTrue(os.path.exists(fkeep))
    self.assertEqual(open(fkeep, 'rb').read(), 'keep')

  #----------------------------------------------------------------------------
  def test_passthru_mkstemp(self):
    with FileSystemOverlay(passthru='.*fso-unittest\\.passthru\\.keep\\..*') as fso:
      kfd, fkeep = tempfile.mkstemp(prefix='fso-unittest.passthru.keep.')
      dfd, fdrop = tempfile.mkstemp(prefix='fso-unittest.passthru.drop.')
      with os.fdopen(kfd, 'wb') as fp:
        fp.write('keep')
      with os.fdopen(dfd, 'wb') as fp:
        fp.write('drop')
    self.assertFalse(os.path.exists(fdrop))
    self.assertTrue(os.path.exists(fkeep))
    self.assertEqual(open(fkeep, 'rb').read(), 'keep')


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
