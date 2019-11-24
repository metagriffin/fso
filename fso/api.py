# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/10/19
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
# $ChangeLog$
#------------------------------------------------------------------------------
