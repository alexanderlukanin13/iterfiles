=========
iterfiles
=========

|pypi| |build| |coverage|

Find and process files in a Pythonic way, without boilerplate code. Implements ``for_each_file`` and other common scenarios.

.. code-block:: python

    >>> from iterfiles import for_each_file
    >>> for_each_file('example', print, pattern='*/*.txt')

This will print all ``*.txt`` file names in all first-level subdirectories of ``example``.

Let's say we have following directory structure:

.. code-block:: text

    example/
        shapes.txt
        aa/
            colors.dat    # not a txt!
            numbers.txt
            pets.txt
        bb/
            names.txt
            cc/
                cars.txt

The output will be:

.. code-block:: text

    example/aa/numbers.txt
    example/aa/pets.txt
    example/bb/names.txt

Filter directories and files via glob()
---------------------------------------

All syntax of `pathlib.Path.glob <https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob>`_ is supported.

Print all ``*.txt`` files in *all* subdirectories:

.. code-block:: python

    >>> for_each_file('example', print, pattern='**/*.txt')
    example/shapes.txt
    example/aa/numbers.txt
    example/aa/pets.txt
    example/bb/names.txt
    example/bb/cc/cars.txt

Print all ``*.txt`` files only in a top-level directory:

.. code-block:: python

    >>> for_each_file('example', print, pattern='*.txt')
    example/shapes.txt


Files as an iterable
--------------------

Iterate over ``pathlib.Path`` objects:

.. code-block:: python

    >>> from iterfiles import iter_files
    >>> [x.name for x in iter_files('example', '**/*.txt')]
    ['shapes.txt', 'numbers.txt', 'pets.txt', 'names.txt', 'cars.txt']

...or over text file contents directly, for example combine the first words from each file:

.. code-block:: python

    >>> from iterfiles import iter_texts
    >>> ', '.join(x.split(' ')[0] for x in iter_texts('example', pattern='**/*.txt'))
    'Square, One, Cat, Alice, Toyota'

Pasting all files together into corpus
--------------------------------------

Use ``for_each_text`` to work with plain text contents directly.

.. code-block:: python

    >>> with open('corpus.txt', 'w') as corpus:
    ...   for_each_text('example', corpus.write, pattern='**/*.txt')

Convert files from one directory to another directory
-----------------------------------------------------

Let's say you want to extract OCR text from a large collection of ``*.pdf`` into ``*.txt`` files.

You have a wonderful function ``pdftotext(pdf_filename, txt_filename)`` from another package,
it does the job well, but how to apply it to a nested directory tree?

.. code-block:: python

    >>> from iterfiles import convert_files
    >>> convert_files('input_pdfs', 'output_txts', pdftotext, pattern='**/*.pdf', rename=lambda p: p.with_suffix('.txt'))

That's all. You'll have the same directory structure in output, and same file names, but with ``*.txt`` suffix instead of ``*.pdf``.

Convert text files
------------------

If both input and output is plain text, use ``convert_texts`` and forget about reading and writing files.
For example, here's a snippet which transforms all files into uppercase:

.. code-block:: python

    >>> from iterfiles import convert_texts
    >>> convert_texts('example', 'output', str.upper, pattern='**/*.txt')


Gotchas and Limitations
-----------------------

* Any unhandled exception raised from your callback will break the loop.
  Make sure to suppress exceptions which are tolerable.
  Error handling (such as logging) is out of scope of this package.

* Collecting a list of files according to a glob pattern happens almost instantly before any processing takes place.
  If you add files to directory during long processing, these new files will not be detected on the fly.
  If you remove files during processing and before they've had a chance to be processed, you will see an error.

* Only files are considered. Directories are traversed in a search for files; and during conversion,
  directories are created when necessary; but that's it. You can't do anything custom with directories.

* Package was not tested with symlinks, and behavior with symlinks is undefined.

Requirements
------------

* Python 3.6+

* No dependencies


.. |pypi| image:: https://img.shields.io/pypi/v/iterfiles.svg
    :target: https://pypi.python.org/pypi/iterfiles
    :alt: pypi

.. |build| image:: https://api.travis-ci.org/alexanderlukanin13/iterfiles.svg?branch=master
    :target: https://travis-ci.org/alexanderlukanin13/iterfiles?branch=master
    :alt: build status

.. |coverage| image:: https://coveralls.io/repos/alexanderlukanin13/iterfiles/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/alexanderlukanin13/iterfiles?branch=master
    :alt: coverage

.. |docs| image:: https://img.shields.io/readthedocs/iterfiles.svg
    :target: http://iterfiles.readthedocs.io/en/latest/
    :alt: documentation
