# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/10/20
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

# todo: move to use `asset` package...

from .isstr import isstr

#------------------------------------------------------------------------------
def resolve(spec):
  if not isstr(spec):
    return spec
  if ':' in spec:
    spec, attr = spec.split(':', 1)
    return getattr(resolve(spec), attr)
  spec = spec.split('.')
  used = spec.pop(0)
  found = __import__(used)
  for cur in spec:
    used += '.' + cur
    try:
      found = getattr(found, cur)
    except AttributeError:
      __import__(used)
      found = getattr(found, cur)
  return found

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
