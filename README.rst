just-start
==========

|Build Status| |Coverage Status| |Waffle.io - Columns and their card count|

An app to defeat procrastination!

Introduction
------------

Just-Start is a to-do list application with a focus on boosting your
productivity and preventing you from procrastinating (too much). It blocks time-
wasting sites while you’re working to help you focus and it can even enable and
disable your wi-fi.

Underneath, it’s basically a wrapper for TaskWarrior_ with a timer implementing
the `Pomodoro Technique`_, a popular time management technique. Currently, the
only client uses the Ncurses_ library and it’s similar to a graphical
application, but in your terminal. More clients are coming soon.

This app draws inspiration from Omodoro_, and the ncurses client, from
Calcurse_.

Supported platforms
-------------------

Linux and macOS for now.

Installation
------------

You need to have Python 3.6 and TaskWarrior_ (a recent enough one) in order for
this to work. To install, just clone this repo and do:

.. code:: bash

    $ pip install -e just-start/

That’s it! This will install an editable/development version (run ``pip install
--help | grep editable`` to find out more). You can of course install without
the ``-e`` flag, but be aware that things still move very fast. You may also
download a release_ instead.

Usage
-----

Just run it from your terminal:

.. code:: bash

    $ just-start

And press h to see a list of available user actions

Development
-----------

If you want to help out, clone the repo and run:

.. code:: bash

    pip install -e just-start/[dev]

This will ensure you have the development and install dependencies.

Running Tests
-------------

First, you’ll need the development_ dependencies. Then, just issue the
following:

.. code:: bash

    pytest --cov=just-start/

.. |Build Status| image:: https://travis-ci.org/AliGhahraei/
   just-start.svg?branch=master
   :target: https://travis-ci.org/AliGhahraei/just-start
.. |Coverage Status| image:: https://coveralls.io/repos/github/AliGhahraei/
   just-start/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/AliGhahraei/just-start?branch=master
.. |Waffle.io - Columns and their card count| image:: https://badge.waffle.io/
   AliGhahraei/just-start.svg?columns=To%20Do,Priority
   :target: https://waffle.io/AliGhahraei/just-start

.. _Calcurse: http://calcurse.org
.. _development: #development
.. _Ncurses: https://www.gnu.org/software/ncurses/
.. _Omodoro: https://github.com/okraits/omodoro
.. _Pomodoro Technique: https://cirillocompany.de/pages/pomodoro-technique
.. _release: https://github.com/AliGhahraei/just-start/releases
.. _Taskwarrior: https://taskwarrior.org/
