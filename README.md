# just-start
[![Build Status](
https://travis-ci.org/AliGhahraei/just-start.svg?branch=master)](
https://travis-ci.org/AliGhahraei/just-start)
[![Coverage Status](
https://coveralls.io/repos/github/AliGhahraei/just-start/badge.svg?branch=master&service=github)](https://coveralls.io/github/AliGhahraei/just-start?branch=master)
[![Waffle.io - Columns and their card count](
https://badge.waffle.io/AliGhahraei/just-start.svg?columns=To%20Do,Priority
)](https://waffle.io/AliGhahraei/just-start)

An app to defeat procrastination!

## Introduction
Just-Start is a to-do list application with a focus on boosting your
productivity and preventing you from procrastinating (too much). It blocks
time-wasting sites while you're working to help you focus and it can even enable
and disable your wi-fi.


Underneath, it's basically a wrapper for [Taskwarrior](https://taskwarrior.org/)
with a timer implementing the 
[Pomodoro Technique](https://cirillocompany.de/pages/pomodoro-technique), a
popular time management technique. Currently, the only client uses the 
[Ncurses](https://www.gnu.org/software/ncurses/) library and it's kind of like
a graphical application, but in your terminal. However, more clients are coming
soon.


This app draws inspiration from [Omodoro](https://github.com/okraits/omodoro)
and the ncurses client, from [Calcurse](http://calcurse.org/).

## Supported platforms
Linux and macOS for now.

## Installation
You need to have Python 3.6 and [Taskwarrior](https://taskwarrior.org/) (a 
recent enough one) in order for this to work. To install, just clone
this repo and do:

```bash
$ pip install -e just-start/
```

That's it! This will install an editable/development version (run `pip install 
--help | grep editable` to find out more). You can of course install without the
`-e` flag, but be aware that things still move very fast. You may also 
download a [release](https://github.com/AliGhahraei/just-start/releases) 
instead.

## Usage
Just run it from your terminal:

```bash
$ just-start
```

And press h to see a list of available user actions

## Development
If you want to help out, clone the repo and run:

```bash
pip install -e just-start/[dev]
```

This will ensure you have the development and install dependencies. 

## Running Tests

First, you'll need the [development](#development) dependencies. Then, just 
issue the following:

```bash
pytest --cov=just-start/
```
