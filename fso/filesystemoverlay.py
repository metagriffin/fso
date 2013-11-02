# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2011/05/15
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import os, __builtin__, six, asset

#------------------------------------------------------------------------------
class UnknownOverlayMode(Exception): pass

#------------------------------------------------------------------------------
class OverlayEntry(object):
  # tbd: i should probably make this into a "file-like" object... that way
  #      an open() can return this object and read's and write's can be checked
  #      immediately...
  TYPE_FILE    = 'file'
  TYPE_DIR     = 'dir'
  TYPE_SYMLINK = 'link'
  TYPE_GHOST   = 'ghost'
  def __init__(self, path, type=TYPE_FILE, content=None):
    #: path: The FS overlay full path, eg. /path/to/filename.ext.
    self.path    = path
    #: type: The FS overlay type, which can be one of OverlayEntry.TYPE_*
    self.type    = type
    #: content: for TYPE_FILE entries, the actual content.
    self.content = content

#------------------------------------------------------------------------------
class ContextStringIO(six.StringIO):
  def __enter__(self):
    return self
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
    return False

#------------------------------------------------------------------------------
class OverlayFileStream(ContextStringIO):
  def __init__(self, overlay, path, *args, **kwargs):
    prepend = kwargs.pop('prepend', '')
    ContextStringIO.__init__(self, *args, **kwargs)
    self.overlay = overlay
    self.path    = path
    self.prepend = prepend
  def close(self):
    self.overlay.entries[self.path] = OverlayEntry(
      self.path, OverlayEntry.TYPE_FILE, self.prepend + self.getvalue())
    ContextStringIO.close(self)

#------------------------------------------------------------------------------
class FileSystemOverlay(object):

  #----------------------------------------------------------------------------
  def __init__(self, install=False):
    self.entries    = {}
    self._installed = False
    self.impostors  = dict()
    self.originals  = dict()
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
    ret = dict(self.entries)
    self.entries.clear()
    return ret

  #----------------------------------------------------------------------------
  def _makeImpostors(self):

    #--------------------------------------------------------------------------
    def fso_open(path, mode=None, buffering=None):
      # tbd: what about *buffering*?...
      if mode is None or 'r' in mode:
        if path in self.entries:
          if self.entries[path].type is OverlayEntry.TYPE_FILE:
            return ContextStringIO(self.entries[path].content)
          if self.entries[path].type is OverlayEntry.TYPE_DIR:
            raise IOError(21, 'Is a directory', path)
          # TBD: assuming self.entries[path].type == 'n'...
          raise IOError(2, 'No such file or directory', path)
        if mode is None:
          return self.originals['__builtin__:open'](path)
        return self.originals['__builtin__:open'](path, mode)
      if 'w' in mode:
        # TBD: check to see if it is a non-file...
        return OverlayFileStream(self, path)
      if 'a' in mode:
        if path not in self.entries and self.originals['os.path:exists'](path):
          # tbd: check to see if it is a readable file instead?
          fp = self.originals['__builtin__:open'](path, 'rb')
          self.entries[path] = OverlayEntry(path, OverlayEntry.TYPE_FILE, fp.read())
          fp.close()
        if path in self.entries:
          return OverlayFileStream(self, path, prepend=self.entries[path].content)
        return OverlayFileStream(self, path)
      raise UnknownOverlayMode(mode)
    self.impostors['__builtin__:open'] = fso_open

    #--------------------------------------------------------------------------
    def fso_makedirs(path, mode=None):
      # TBD: implement file hierarchies in self.entries!...
      pass
    self.impostors['os:makedirs'] = fso_makedirs

    #--------------------------------------------------------------------------
    def fso_exists(path):
      if path in self.entries:
        return self.entries[path].type is not OverlayEntry.TYPE_GHOST
      return self.originals['os.path:exists'](path)
    self.impostors['os.path:exists'] = fso_exists

    #--------------------------------------------------------------------------
    def fso_access(path, mode):
      if path in self.entries:
        # TBD: implement better file access control...
        # TBD: make this dependent on entry.type!...
        return True
      return self.originals['os:access'](path, mode)
    self.impostors['os:access'] = fso_access

    #--------------------------------------------------------------------------
    def fso_unlink(path):
      self.entries[path] = OverlayEntry(path, OverlayEntry.TYPE_GHOST, None)
    self.impostors['os:unlink'] = fso_unlink

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
