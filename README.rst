===================
File System Overlay
===================

File System Overlay (FSO) allows *side-effect free* unit testing of
file I/O operations. It does this by creating a caching overlay over
the local file system, allowing read-through access, but storing
modifications in memory. These in-memory changes can be inspected, to
validate unit tests, and when the test completes, all changes to the
file system will be vaporized (to quote Dr. Stanley Goodspeed:
http://www.youtube.com/watch?v=K-uEbYq9kNU&t=6m29s).


Project
=======

* Homepage: https://github.com/metagriffin/fso
* Bugs: https://github.com/metagriffin/fso/issues


TL;DR
=====

Install:

.. code-block:: bash

  $ pip install fso

Use:

.. code-block:: python

  import unittest, fso

  class MyTest(unittest.TestCase):

    def setUp(self):
      fso.push()

    def tearDown(self):
      fso.pop()

    def test_fs_changes(self):

      self.assertFalse(os.path.exists('/etc/foobar.conf'))

      with open('/etc/foobar.conf', 'wb') as fp:
        fp.write('some-data')

      self.assertTrue(os.path.exists('/etc/foobar.conf'))
      self.assertEqual(open('/etc/foobar.conf', 'rb').read(), 'some-data')

      # BUT, when testing ends, /etc/foobar.conf will not exist! *awesome*! :)

      # you can also check that the expected changes are there (noting
      # that all paths are absolutized, dereferenced, and normalized):
      self.assertEqual(fso.changes, [
        'add:/etc/foobar.conf',
        ])


Overview
========

Traditionally, testing I/O operations on the file system requires
modifying the implementation so that there is a pluggable layer of
file operations that gets replaced with mocks when performing tests
(http://stackoverflow.com/questions/2655697/python-unittest-howto).

This is, IMHO, a terrible approach, since it means that the real code
is not being executed, and may well hide some very real bugs.

As an alternative, the FSO package switches out the implementation of
the low-level file system calls, and caches changes in-memory, never
actually modifying the file system.

Although this is a very "pure" approach, there are *many* gotchas...
So, currently, only very basic file operations are supported (such as
writing to a new file) -- if you are doing more complex things, FSO is
not ready for you yet! But, if you don't mind, please help identify
those holes by either reporting issues or providing patches... any
contributions will be merged and very much appreciated!


Supported Operations
====================

Currently, only the following I/O functions have replacements
implemented:

* builtin.open
* os.symlink
* os.stat
* os.lstat
* os.unlink
* os.remove
* os.listdir
* os.mkdir
* os.makedirs
* os.rmdir
* os.path.exists
* os.path.lexists

* os.access

Most other I/O operations are built on top of these, so they
implicitly work with FSO. **However**, because they use whatever
instrumented functions are currently in the global scope, this means
that they are not compatible with *multiple* levels of FSO overlays.
Since that is not the typical FSO use-case, this is deemed an
acceptable trade-off.

Examples of I/O operations that are supported, but only when using a
single active FSO layer:

* os.walk
* os.path.isdir
* os.path.isfile
* os.path.islink (on posix and windows -- *maybe* apple? who really cares?)


Known Limitations
=================

* The current implementation is very "bare bones" -- user be warned!
* File permissions are currently NOT enforced (and might be overkill).
* Since changes are explicitly stored in-memory, changes that exceed
  the local machine's memory will cause problems.
* The following categories of filesystem entries will not work:
  * sockets
  * block special device files
  * character special device files
  * FIFOs (named pipes)

Usage
=====

FSO supports context managers! In most cases, this is actually
recommend. The reason is that some unit testing frameworks, such as
nose, do not report errors very well if an FSO layer is still
active. Using the context manager will ensure that the FSO is
uninstalled before they need to report the errors. Example:

.. code-block:: python

  import unittest, fso

  class TestWithContextManager(unittest.TestCase):

    def test_with_cm(self):

      self.assertFalse(os.path.exists('no-such-file'))

      with fso.push() as overlay:

        self.assertFalse(os.path.exists('no-such-file'))

        with open('no-such-file', 'wb') as fp:
          fp.write('created')

        os.unlink('/etc/hosts')
        os.mkdir('/tmp/my-test-directory')

        self.assertTrue(os.path.exists('no-such-file'))
        self.assertEqual(overlay.changes, [
          'del:/etc/hosts',
          'add:/path/to/cwd/no-such-file',
          'add:/tmp/my-test-directory',
          ])

      self.assertFalse(os.path.exists('no-such-file'))
      self.assertFalse(os.path.exists('/etc/my-test-directory'))
      self.assertTrue(os.path.exists('/etc/hosts'))

