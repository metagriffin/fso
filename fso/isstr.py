# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/10/20
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import sys
PY3 = sys.version_info[0] == 3

if PY3:
  def isstr(obj):
    return isinstance(obj, str)
else:
  def isstr(obj):
    return isinstance(obj, basestring)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
