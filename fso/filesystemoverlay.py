# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2011/05/15
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

# TODO: add support for all kinds of file types besides REG and LNK, ie:
#         stat.S_ISCHR(mode)    == character special device file
#         stat.S_ISBLK(mode)    == block special device file
#         stat.S_ISFIFO(mode)   == FIFO (named pipe)
#         stat.S_ISSOCK(mode)   == socket

import sys, os, six, asset, stat, collections

#------------------------------------------------------------------------------
class UnknownOverlayMode(Exception): pass

#------------------------------------------------------------------------------
OverlayStat = collections.namedtuple('OverlayStat', [
  'st_mode', 'st_ino', 'st_dev', 'st_nlink', 'st_uid', 'st_gid',
  'st_size', 'st_atime', 'st_mtime', 'st_ctime', 'st_overlay'])

#------------------------------------------------------------------------------
class ContextStringIO(six.StringIO):
  def __enter__(self):
    return self
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
    return False

#------------------------------------------------------------------------------
class OverlayFileStream(ContextStringIO):
  def __init__(self, fso, path, *args, **kwargs):
    prepend = kwargs.pop('prepend', '')
    ContextStringIO.__init__(self, *args, **kwargs)
    self.fso     = fso
    self.path    = path
    self.prepend = prepend
  def close(self):
    self.fso._addentry(OverlayEntry(
      self.fso, self.path, stat.S_IFREG, self.prepend + self.getvalue()))
    ContextStringIO.close(self)

#------------------------------------------------------------------------------
class OverlayEntry(object):
  # todo: i should probably make this into a "file-like" object... that way
  #       an open() can return this object and read's and write's can be checked
  #       immediately...
  def __init__(self, fso, path, mode=stat.S_IFREG, content=None, omode=None):
    self.fso     = fso
    #: path: The FS overlay full path, eg. /path/to/filename.ext.
    self.path    = path
    #: mode: The FS overlay entry type, which can be one of stat.S_IF*
    self.mode    = mode
    #: content: for S_IFREG entries, the actual content, for S_IFLNK
    #:          entries, the target of the link.
    self.content = content
    #: omode: the overlayed entry type, if it existed
    self.omode   = omode
  @property
  def stat(self):
    if self.mode is None:
      raise OSError(2, 'No such file or directory', self.path)
    size = len(self.content or '')
    return OverlayStat(
      st_mode=self.mode, st_size=size, st_overlay=1,
      # todo: if possible, inherit these from the original entry...
      st_ino=0, st_dev=0, st_nlink=0, st_uid=0, st_gid=0,
      st_atime=0, st_mtime=0, st_ctime=0)
  @property
  def change(self):
    if self.mode is None:
      return 'del:' + self.path
    if self.omode is None:
      return 'add:' + self.path
    return 'mod:' + self.path
  def __repr__(self):
    return '<OverlayEntry %s mode=%r, omode=%r, content-length=%d>' % (
      self.path, self.mode, self.omode, len(self.content or ''))

#------------------------------------------------------------------------------
class FileSystemOverlay(object):

  mapping = {

    # note that many of the following are (in the python platform)
    # implemented to use other functions that *are* already overlayed,
    # so in theory they should not need overlaying... *HOWEVER*,
    # because they are not overlay sensitive, the pop out to the
    # currently installed overlay, and therefore are not multi-overlay
    # compatible... ugh. perhaps this multi-overlay is just not worth
    # it.

    '__builtin__:open'  : 'fso_open',
    'os:unlink'         : 'fso_unlink',
    'os:remove'         : 'fso_remove',
    'os:readlink'       : 'fso_readlink',
    'os:stat'           : 'fso_stat',
    'os:lstat'          : 'fso_lstat',
    'os:symlink'        : 'fso_symlink',
    'os:listdir'        : 'fso_listdir',
    'os:mkdir'          : 'fso_mkdir',
    'os:makedirs'       : 'fso_makedirs',
    'os:rmdir'          : 'fso_rmdir',
    'os:access'         : 'fso_access',
    'os.path:exists'    : 'fso_exists',
    'os.path:lexists'   : 'fso_lexists',
    'os.path:islink'    : 'fso_islink',
    'shutil:rmtree'     : 'fso_rmtree',
    }

  #----------------------------------------------------------------------------
  def __init__(self, install=False):
    self.entries    = {}
    self._installed = False
    self.impostors  = dict()
    self.originals  = dict()
    self.vaporized  = None
    self._makeImpostors()
    if install:
      self.install()

  #----------------------------------------------------------------------------
  @property
  def installed(self):
    return self._installed

  #----------------------------------------------------------------------------
  @property
  def active(self):
    if not self._installed:
      return False
    for symbol, handle in self.impostors.items():
      mod, attr = symbol.split(':', 1)
      mod = asset.symbol(mod)
      if getattr(mod, attr) is not handle:
        return False
    return True

  #----------------------------------------------------------------------------
  def __enter__(self):
    return self.install()

  #----------------------------------------------------------------------------
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.uninstall()
    return False

  #----------------------------------------------------------------------------
  def install(self):
    if self.installed:
      if not self.active:
        raise TypeError('FileSystemOverlay 0x%x install collision' % (id(self),))
      return self
    if len(self.originals) != 0:
      raise ValueError('i-rep violation: `self.originals` is not empty')
    self._installed = True
    for symbol, handle in self.impostors.items():
      mod, attr = symbol.split(':', 1)
      mod = asset.symbol(mod)
      self.originals[symbol] = getattr(mod, attr)
      setattr(mod, attr, handle)
    return self

  #----------------------------------------------------------------------------
  def uninstall(self):
    if not self.installed:
      return self
    if not self.active:
      raise TypeError('FileSystemOverlay 0x%x uninstall order violation' % (id(self),))
    self._installed = False
    for symbol, handle in self.originals.items():
      mod, attr = symbol.split(':', 1)
      mod = asset.symbol(mod)
      setattr(mod, attr, handle)
    self.originals.clear()
    self.vaporized = dict(self.entries)
    self.entries.clear()
    return self.vaporized

  #----------------------------------------------------------------------------
  def _makeImpostors(self):
    if self.impostors:
      raise ValueError('impostors have already been populated')
    for orig, impost in self.mapping.items():
      self.impostors[orig] = getattr(self, impost)
    return self

  #----------------------------------------------------------------------------
  @property
  def changes(self):
    return [self.entries[path].change for path in sorted(self.entries.keys())]

  #----------------------------------------------------------------------------
  @property
  def diff(self):
    # TODO: implement...
    raise NotImplementedError()

  #----------------------------------------------------------------------------
  def _addentry(self, entry):
    if entry.path in self.entries:
      entry.omode = self.entries[entry.path].omode
      if entry.mode is None and entry.omode is None:
        del self.entries[entry.path]
        return
    else:
      try:
        entry.omode = stat.S_IFMT(self.originals['os:lstat'](entry.path).st_mode)
      except Exception:
        pass
    self.entries[entry.path] = entry

  #############################################################################

  #----------------------------------------------------------------------------
  def abs(self, path):
    # TODO: on windows, convert '\\' to '/'...
    return os.path.abspath(path)

  #----------------------------------------------------------------------------
  def deref(self, path, to_parent=False):
    # TODO: make this work for windows too...
    path = self.abs(path)
    if to_parent:
      head, tail = os.path.split(path)
      return os.path.join(self.deref(head), tail)
    # TODO: root on windows... ugh.
    curpath  = '/'
    segments = path.split('/')
    for idx, seg in enumerate(segments):
      curpath = os.path.join(curpath, seg)
      st = self._lstat(curpath)
      if stat.S_ISLNK(st.st_mode):
        target = os.path.join(os.path.dirname(curpath), self.fso_readlink(curpath))
        target = os.path.join(target, *segments[idx + 1:])
        return self.deref(target)
    return os.path.join('/', *segments)

  #----------------------------------------------------------------------------
  def _stat(self, path):
    '''IMPORTANT: expects `path`'s parent to already be deref()'erenced.'''
    if path not in self.entries:
      return OverlayStat(*self.originals['os:stat'](path)[:10], st_overlay=0)
    st = self.entries[path].stat
    if stat.S_ISLNK(st.st_mode):
      return self._stat(self.deref(path))
    return st

  #----------------------------------------------------------------------------
  def _lstat(self, path):
    '''IMPORTANT: expects `path`'s parent to already be deref()'erenced.'''
    if path not in self.entries:
      return OverlayStat(*self.originals['os:lstat'](path)[:10], st_overlay=0)
    return self.entries[path].stat

  #----------------------------------------------------------------------------
  def fso_anystat(self, path, link):
    # TODO: what about if path == '/'...
    # TODO: make this work for windows too...
    # steps:
    #   - ensure that all directory components to dirname(path)
    #     exist and are directories
    #   - then check the file itself
    path = self.abs(path)
    head, tail = os.path.split(path)
    head = self.deref(head)
    st   = self._stat(head)
    if not stat.S_ISDIR(st.st_mode):
      raise OSError(20, 'Not a directory', path)
    if link:
      return self._lstat(os.path.join(head, tail))
    return self._stat(os.path.join(head, tail))

  #----------------------------------------------------------------------------
  def fso_lstat(self, path):
    'overlays os.lstat()'
    return self.fso_anystat(path, link=True)

  #----------------------------------------------------------------------------
  def fso_stat(self, path):
    'overlays os.stat()'
    return self.fso_anystat(path, link=False)

  #----------------------------------------------------------------------------
  def _exists(self, path):
    '''IMPORTANT: expects `path` to already be deref()'erenced.'''
    try:
      return bool(self._stat(path))
    except os.error:
      return False

  #----------------------------------------------------------------------------
  def _lexists(self, path):
    '''IMPORTANT: expects `path` to already be deref()'erenced.'''
    try:
      return bool(self._lstat(path))
    except os.error:
      return False

  #----------------------------------------------------------------------------
  def fso_exists(self, path):
    'overlays os.path.exists()'
    try:
      return self._exists(self.deref(path))
    except os.error:
      return False

  #----------------------------------------------------------------------------
  def fso_lexists(self, path):
    'overlays os.path.lexists()'
    try:
      return self._lexists(self.deref(path, to_parent=True))
    except os.error:
      return False

  #----------------------------------------------------------------------------
  def fso_listdir(self, path):
    'overlays os.listdir()'
    path = self.deref(path)
    if not stat.S_ISDIR(self._stat(path).st_mode):
      raise OSError(20, 'Not a directory', path)
    try:
      ret = self.originals['os:listdir'](path)
    except Exception:
      # assuming that `path` was created within this FSO...
      ret = []
    for entry in self.entries.values():
      if not entry.path.startswith(path + '/'):
        continue
      subpath = entry.path[len(path) + 1:]
      if '/' in subpath:
        continue
      if entry.mode is None:
        if subpath in ret:
          ret.remove(subpath)
      else:
        if subpath not in ret:
          ret.append(subpath)
    return ret

  #----------------------------------------------------------------------------
  def fso_mkdir(self, path, mode=None):
    'overlays os.mkdir()'
    path = self.deref(path, to_parent=True)
    if self._lexists(path):
      raise OSError(17, 'File exists', path)
    self._addentry(OverlayEntry(self, path, stat.S_IFDIR))

  #----------------------------------------------------------------------------
  def fso_makedirs(self, path, mode=None):
    'overlays os.makedirs()'
    path = self.abs(path)
    cur = '/'
    segments = path.split('/')
    for idx, seg in enumerate(segments):
      cur = os.path.join(cur, seg)
      try:
        st = self.fso_stat(cur)
      except OSError:
        st = None
      if st is None:
        self.fso_mkdir(cur)
        continue
      if idx + 1 == len(segments):
        raise OSError(17, 'File exists', path)
      if not stat.S_ISDIR(st.st_mode):
        raise OSError(20, 'Not a directory', path)

  #----------------------------------------------------------------------------
  def fso_rmdir(self, path):
    'overlays os.rmdir()'
    st = self.fso_lstat(path)
    if not stat.S_ISDIR(st.st_mode):
      raise OSError(20, 'Not a directory', path)
    if len(self.fso_listdir(path)) > 0:
      raise OSError(39, 'Directory not empty', path)
    self._addentry(OverlayEntry(self, path, None))

  #----------------------------------------------------------------------------
  def fso_readlink(self, path):
    'overlays os.readlink()'
    path = self.deref(path, to_parent=True)
    st = self.fso_lstat(path)
    if not stat.S_ISLNK(st.st_mode):
      raise OSError(22, 'Invalid argument', path)
    if st.st_overlay:
      return self.entries[path].content
    return self.originals['os:readlink'](path)

  #----------------------------------------------------------------------------
  def fso_symlink(self, source, link_name):
    'overlays os.symlink()'
    path = self.deref(link_name, to_parent=True)
    if self._exists(path):
      raise OSError(17, 'File exists')
    self._addentry(OverlayEntry(self, path, stat.S_IFLNK, source))

  #----------------------------------------------------------------------------
  def fso_unlink(self, path):
    'overlays os.unlink()'
    path = self.deref(path, to_parent=True)
    if not self._lexists(path):
      raise OSError(2, 'No such file or directory', path)
    self._addentry(OverlayEntry(self, path, None))

  #----------------------------------------------------------------------------
  def fso_remove(self, path):
    'overlays os.remove()'
    return self.fso_unlink(path)

  #----------------------------------------------------------------------------
  def fso_islink(self, path):
    'overlays os.path.islink()'
    try:
      return stat.S_ISLNK(self.fso_lstat(path).st_mode)
    except OSError:
      return False

  #----------------------------------------------------------------------------
  def fso_rmtree(self, path, ignore_errors=False, onerror=None):
    'overlays shutil.rmtree()'
    if ignore_errors:
      def onerror(*args):
        pass
    elif onerror is None:
      def onerror(*args):
        raise
    try:
      if self.fso_islink(path):
        # symlinks to directories are forbidden, see shutil bug #1669
        raise OSError('Cannot call rmtree on a symbolic link')
    except OSError:
      onerror(os.path.islink, path, sys.exc_info())
      # can't continue even if onerror hook returns
      return
    names = []
    try:
      names = self.fso_listdir(path)
    except os.error, err:
      onerror(os.listdir, path, sys.exc_info())
    for name in names:
      fullname = os.path.join(path, name)
      try:
        mode = self.fso_lstat(fullname).st_mode
      except os.error:
        mode = 0
      if stat.S_ISDIR(mode):
        self.fso_rmtree(fullname, ignore_errors, onerror)
      else:
        try:
          self.fso_remove(fullname)
        except OSError as err:
          onerror(os.remove, fullname, sys.exc_info())
    try:
      self.fso_rmdir(path)
    except os.error:
      onerror(os.rmdir, path, sys.exc_info())

  #----------------------------------------------------------------------------
  def fso_open(self, path, mode=None, buffering=None):
    # todo: what about `buffering`?...
    # todo: pass `mode` to ContextStringIO/OverlayFileStream so
    #       that other params can be leveraged? eg. 'b' / '+' / 'U'...

    if mode is None:
      mode = 'r'
    head, tail = os.path.split(path)
    try:
      head = self.deref(head)
    except OSError:
      raise IOError(2, 'No such file or directory', path)
    st   = self._stat(head)
    if not stat.S_ISDIR(st.st_mode):
      raise IOError(2, 'No such file or directory', path)
    path = os.path.join(head, tail)

    # todo: do better sanity checking of 'mode'...

    if 'r' in mode and ( 'w' in mode or 'a' in mode ) or '+' in mode:
      # TODO: remove this restriction...
      raise ValueError('unsupported FSO mode %s' % (mode,))

    if 'r' not in mode and 'w' not in mode and 'a' not in mode:
      raise UnknownOverlayMode(mode)

    # todo: perhaps all operations should return an OverlayStream
    #       so that "accidental" writes on a 'r' declared fp are
    #       caught?... is that even a possible problem?

    # read
    if 'r' in mode:
      try:
        path = self.deref(path)
        st = self._stat(path)
      except OSError:
        raise IOError(2, 'No such file or directory', path)
      if stat.S_ISDIR(st.st_mode):
        raise IOError(21, 'Is a directory', path)
      if not stat.S_ISREG(st.st_mode):
        raise IOError(2, 'No such file or directory', path)
      if path in self.entries:
        return ContextStringIO(self.entries[path].content)
      return self.originals['__builtin__:open'](path, mode)

    # write/append

    # dereference all symlinks up until the tail is either a file or non-existent
    while True:
      head, tail = os.path.split(path)
      try:
        head = self.deref(head)
      except OSError:
        raise IOError(2, 'No such file or directory', path)
      path = os.path.join(head, tail)
      try:
        st = self._lstat(path)
      except OSError:
        # the file does not exist -- swith 'a' to 'w' (if currently 'a')
        if 'a' in mode:
          mode = mode.replace('a', '')
        if 'w' not in mode:
          mode = 'w' + mode
        break
      if stat.S_ISREG(st.st_mode):
        break
      if stat.S_ISLNK(st.st_mode):
        path = os.path.join(head, self.fso_readlink(path))
        continue
      raise IOError(21, 'FSO ERROR: unexpected stat while write/append', path)

    # write
    if 'a' not in mode:
      return OverlayFileStream(self, path)

    # append
    if path in self.entries:
      if self.entries[path].mode is None:
        # note: this should never happen -- lstat() should have raised OSError()
        return OverlayFileStream(self, path)
      return OverlayFileStream(self, path, prepend=self.entries[path].content)

    with self.originals['__builtin__:open'](path, 'rb') as fp:
      return OverlayFileStream(self, path, prepend=fp.read())

  #############################################################################

  #----------------------------------------------------------------------------
  def fso_access(self, path, mode):
    raise NotImplementedError()
    # if path in self.entries:
    #   # TODO: implement better file access control...
    #   # TODO: make this dependent on entry.mode!...
    #   return True
    # return self.originals['os:access'](path, mode)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
