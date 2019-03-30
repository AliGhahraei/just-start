just-start
==========

|Build Status| |Coverage Status| |Waffle.io - Columns and their card count|

An app to defeat procrastination!

Introduction
------------

Just-Start is a to-do list application and productivity booster. It prevents
you from procrastinating (too much).

The program is a wrapper for TaskWarrior_ with a timer implementing the
`Pomodoro Technique`_ (time management). It also draws a bit of inspiration from
Omodoro_.

Features:

- Configurable pomodoro phase durations
- Support for multiple configurations (a.k.a. *locations*) based on the current time and day of the week
- Desktop notifications
- Block time-wasting sites while you’re working

Installation
------------

Supported platforms:

- Linux
- macOS

Requirements:

- Python 3.7
- TaskWarrior_ (latest)

Clone this repo and run the following replacing <client_name> with a name from
the Clients_ table:

.. code:: bash

    $ pip install -e just-start[<client_name>]

So, for example, this would install the urwid client:

.. code:: bash

    $ pip install -e just-start[urwid]

Now go to Usage_

This installs an editable/development version (run ``pip install --help | grep
 --after-context=4 -- --editable`` to find out more). You can of course install
without the ``-e`` flag, but be aware that things still move very fast. You may
also download a release_ instead.

Clients
-------

+------+----------+------------------------------------------------------------+
|Name  |Framework |Notes                                                       |
+======+==========+============================================================+
|urwid |Urwid_    |Inspired by Calcurse_. Similar to a graphical               |
|      |          |application, but in your terminal                           |
+------+----------+------------------------------------------------------------+
|term  |Terminal  |Example client. Useful for seeing how to write a brand new  |
|      |(none)    |one but not intended for continuous usage                   |
+------+----------+------------------------------------------------------------+

Usage
-----

.. code:: bash

    $ just-start-<client_name>

So for the urwid client:

.. code:: bash

    $ just-start-urwid

Press h to see a list of available user actions.

Development
-----------

If you want to help out please install Pipenv_, clone the repo and run:

.. code:: bash

    $ cd just-start/
    $ pipenv install --dev -e .

This will ensure you have both the development and install dependencies.

Issues are tracked using Waffle_ + `GitHub Issues`_

Running Tests
-------------

First, you’ll need the Development_ dependencies. Then, just issue the
following:

.. code:: bash

    $ coverage run --source=just_start,just_start_urwid -m pytest; coverage report

.. |Build Status| image:: https://travis-ci.org/AliGhahraei/
   just-start.svg?branch=master
   :target: https://travis-ci.org/AliGhahraei/just-start
.. |Coverage Status| image:: https://codecov.io/gh/AliGhahraei/just-start/branch
   /master/graph/badge.svg
   :target: https://codecov.io/gh/AliGhahraei/just-start
.. |Waffle.io - Columns and their card count| image:: https://badge.waffle.io/
   AliGhahraei/just-start.svg?columns=To%20Do,Priority
   :target: https://waffle.io/AliGhahraei/just-start

.. _Calcurse: http://calcurse.org
.. _GitHub Issues: https://github.com/AliGhahraei/just-start/issues
.. _Omodoro: https://github.com/okraits/omodoro
.. _Pipenv: https://docs.pipenv.org
.. _Pomodoro Technique: https://cirillocompany.de/pages/pomodoro-technique
.. _release: https://github.com/AliGhahraei/just-start/releases
.. _Taskwarrior: https://taskwarrior.org/
.. _Urwid: http://urwid.org/
.. _Waffle: https://waffle.io/AliGhahraei/just-start
