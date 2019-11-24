=========
ChangeLog
=========


v0.3.2
======

* Deprecated `FSO.getChanges` in favor of `FSO.get_changes`
* Added `FSO.apply` helper method


v0.3.1
======

* Removed `distribute` dependency


v0.3
====

* Stubbed support for "bufsize" parameter to os.fdopen


v0.2
====

* First tagged release
* Added `passthru` option to exclude overlayed paths
* Added preliminary support for file descriptor based access via:
  - os.open()
  - os.fdopen()
  - os.write()
  - os.read()
  - os.close()
