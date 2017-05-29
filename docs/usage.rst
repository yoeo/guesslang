Usage
=====

.. toctree::
   :maxdepth: 2

This is Guesslang command line interface user guide.

To list all the available options, please run:

.. code-block:: python
  :linenos:

  guesslang --help

Detect programming languages
----------------------------

To detect the programming language of a source file
you can run the following command:

.. code-block:: shell
  :linenos:

  # Prints the language name
  guesslang -i /path/to/file

You can also directly write the source code on the console:

.. code-block:: shell
  :linenos:

  guesslang
  # ↓↓↓  Write your source code here. End with CTR^D  ↓↓↓

or send the source code to Guesslang through a ``|`` pipe:

.. code-block:: shell
  :linenos:

  command-that-prints-code | guesslang

With ``--all`` option, you can list all the programming languages
that may match your source code:

.. code-block:: shell
  :linenos:

  # Prints the languages list
  guesslang --all -i /path/to/ambiguous-source-file

Examples
^^^^^^^^

* Detect the programming language of ``/bin/which``:

.. code-block:: shell
  :linenos:

  guesslang -i /bin/which

  # >>> The source code is written in Shell

* Detect the programming language from a text:

.. code-block:: shell
  :linenos:

  echo '
  /** Turn command line arguments to uppercase */
  object Main {
    def main(args: Array[String]) {
      val res = for (a <- args) yield a.toUpperCase
      println("Arguments: " + res.toString)
    }
  }
  ' | guesslang

  # >>> The source code is written in Scala

* Detect the programming languages of a source code that embeds
  an other source code (`sourcecodeception <http://explosm.net/comics/1605/>`_):

.. code-block:: shell
  :linenos:

  echo '
  from __future__ import print_function


  def dump_code(code):
    print(code)


  if __name__ == "__main__":
      dump_code("""
          #include<stdio.h>

          int main(int argc, char** argv)
          {
            char* command = argv[0];
            printf("%s - %d args\n", command, --argc);
            return 0;
          }
      """
      )

  ' | guesslang --all

  # >>> The source code is written in Python or C

.. _create-model:

Create you own Guesslang model
------------------------------

Guesslang uses a trained machine learning model
to detect the programming languages (more details here -- :doc:`how`).

You can train your own Guesslang model using a set of source files:

.. code-block:: shell
  :linenos:

  guesslang --model /path/to/my-model --learn /path/to/training-files

After training your model, you can check its accuracy with this command:

.. code-block:: shell
  :linenos:

  # A detailed test report file is generated
  guesslang --model /path/to/my-model --test /path/to/test-files

Finally you can detect programming languages using your own model
by setting the ``--model`` option:

.. code-block:: shell
  :linenos:

  guesslang --model /path/to/my-model -i /path/to/file

Guesslang tools
---------------

Guesslang is distributed with a set of tools that will allow you to rebuild
the default model from scratch. This is useful when you want to support
new programming languages.

You can add / remove languages by editing the supported languages list
located at ``config/languages.json``.

.. warning::

  Additional dependencies are required to run Guesslang tools:

  .. code-block:: shell
    :linenos:

    pip3 install -r requirements-dev.txt

Github repositories downloader
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You need thousands of source files to train and test a Guesslang model.
To fetch the required files you can use
Guesslang's Github repositories downloader:

.. code-block:: shell
  :linenos:

  # The zipped repositories are saved into /path/to/repo
  tools/download_github_repo.py my-github-oauth-token /path/to/repo

Learning & Test files extractor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After downloading the repositories you can extract the required files
to create your ``learning`` and your ``test`` data sets:

.. code-block:: shell
  :linenos:

  tools/unzip_repos.py /path/to/repo /path/to/extracted-files
  # the following subdirectories are created in
  # /path/to/extracted-files/:
  # │
  # ├─ learn/
  # └─ test/

Keywords creator
^^^^^^^^^^^^^^^^

The next step is to build a ``most common words dictionary`` or ``keywords``
from you ``learning`` files:

.. code-block:: shell
  :linenos:

  tools/make_keywords.py /path/to/extracted-files/learn /path/to/keywords.json

Then replace the default ``keywords`` located at ``config/keywords.json``
with the ones you just created:

.. code-block:: shell
  :linenos:

  mv config/keywords.json config/keywords.json.bkp  # backup default keywords
  mv /path/to/keywords.json config/keywords.json

.. note::

  With the new ``keywords`` and the extracted files, you can create and test
  your new Guesslang model -- :ref:`create-model`.

Accuracy visualizer
^^^^^^^^^^^^^^^^^^^

A detailed report file is generated during the model test.

Using this file, you can display an interactive graph that shows
the accuracy per language of your Guesslang model:

.. code-block:: shell
  :linenos:

  tools/report_graph.py /path/to/report.json

A well-trained model should produce a diagonal matrix like this one:

.. figure:: _static/images/co-occurrence.png
  :alt: Test report
