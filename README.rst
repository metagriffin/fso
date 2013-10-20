===================
File System Overlay
===================

.. warning::

  2013/10/19: FSO is currently under active development - come back in a
  couple of weeks.


File System Overlay (FSO) allows side-effect unit testing of file I/O
operations. It does this by creating an overlay over the local file
system which allows read-through access, but stores write operations
in memory. These in-memory changes can be inspected, to validate unit
tests, and when the test ends, all changes to the file system will
vaporize (to quote Dr. Stanley Goodspeed).


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


Overview
========

Traditionally, testing I/O operations on the file system requires
modifying the implementation so that there is a pluggable layer of
file operations that gets replaced with mocks when performing tests
(http://stackoverflow.com/questions/2655697/python-unittest-howto).

This is, IMHO, a terrible approach, since it means that the real code
is not being executed, and may well hide some very real bugs.

Instead, the `fso` package switches out the implementation of the
low-level file system calls, and caches changes in-memory, never
actually modifying the file system.

Although this is a very "pure" approach, there are *many* gotchas...
So, currently, only very basic file operations are supported (such as
writing to a new file) -- if you are doing more complex things, fso is
not ready for you yet! But, if you don't mind, please help identify
those holes by either reporting issues or providing patches... any
contributions will be merged and very much appreciated!


Supported Operations
====================

Currently, only the following methods are implemented:

* builtin.open
* os.path.exists
* os.makedirs
* os.access
* os.unlink


Unsupported Operations
======================

The following need to be implemented in order to bring I/O coverage to
a respectable minimum:

* os.stat
* os.path.isdir (might be covered by os.stat?)
* os.path.isfile (might be covered by os.stat?)
* os.path.islink (might be covered by os.stat?)
* os.listdir


Known Limitations
=================

* File permissions are currently NOT enforced.
* Since changes are explicitly stored in-memory, changes that exceed
  the local machine's memory will cause problems.


Usage
=====

FSO supports context managers! Example:

.. code-block:: python

  import unittest, fso

  class TestWithContextManager(unittest.TestCase):

    def test_with_cm(self):

      self.assertFalse(os.path.exists('no-such-file'))

      with fso.push() as overlay:

        self.assertFalse(os.path.exists('no-such-file'))

        with open('no-such-file', 'wb') as fp:
          fp.write('created')

        self.assertTrue(os.path.exists('no-such-file'))
        self.assertEqual(len(overlay.entries), 1)
        entry = overlay.entries.values()[0]
        self.assertEqual(entry.path, 'no-such-file')
        self.assertEqual(entry.type, 'file')
        self.assertEqual(entry.content, 'created')

      self.assertFalse(os.path.exists('no-such-file'))
