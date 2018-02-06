# just-start
An app to defeat procrastination.

## Introduction
Just-Start is a to-do list application with a focus on boosting your productivity and preventing 
you from procrastinating (too much). It blocks time-wasting sites while you're working to help you
focus and it can even enable and disable your wi-fi.


Underneath, it's basically a wrapper for [Taskwarrior](https://taskwarrior.org/) with a timer
implementing the [Pomodoro Technique](https://cirillocompany.de/pages/pomodoro-technique), a
popular time management technique.
It uses ncurses (so it's kind of like a graphical application, but in your terminal).


This app draws inspiration from [Omodoro](https://github.com/okraits/omodoro) and a bit from [Calcurse](http://calcurse.org/).

## Supported platforms
Linux and macOS for now.

## Installation
You need to have Python 3.6 and [Taskwarrior](https://taskwarrior.org/) (a recent enough one) in
order for this to work.
To install, just download/clone this repo or its latest release and do:

```
$ pip install just-start/
```

That's it!

## Usage
Just run it from your terminal:

```
$ just-start
```
