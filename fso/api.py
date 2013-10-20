# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/10/19
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

from .filesystemoverlay import FileSystemOverlay

__all__ = 'push', 'pop'

_stack = []

#------------------------------------------------------------------------------
def push(fso=None):
  if fso is None:
    fso = FileSystemOverlay(install=False)
  if fso.active:
    assert _stack[-1] is fso
    return fso
  if fso.installed:
    raise ValueError('cannot multi-interleave FileSystemOverlay installations')
  _stack.append(fso)
  return fso.install()

#------------------------------------------------------------------------------
def pop():
  return _stack.pop().uninstall()

#------------------------------------------------------------------------------
def peek():
  if len(_stack) <= 0:
    return None
  return _stack[-1]

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
