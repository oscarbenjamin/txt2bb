TXT2BB
======

A simple utility for writing questions in plain text that can be imported as
question "pools" in Blackboard when making online tests. The tests can be
written and viewed locally in latex before converting to Blackboard format and
uploading.


Format
------

The idea is that you write a file called e.g. questions.txt that looks
something like
```
# Here are a load of questions
# These lines are comments
# Blank lines are ignored

------------------ Question

type: MA
prompt: Which of these ODEs is linear?
correct: $\frac{dx}{dt} + x$
correct: $\frac{dx}{dt} + \cos{t}$
incorrect: $\frac{dx}{dt} + \cos{x}$
incorrect: $\frac{dy}{dt} + y^2$

------------------ Question

type: MC
prompt: What is the general solution of $\frac{dx}{dt} = x$?
correct: $C\mathrm{e}^t$
incorrect: $C\sin{t}$
incorrect: $C\cos{t}$
incorrect: $C\log{t}$
```
See the provided questions.txt file for examples.

Usage
-----

Once you have your questions written up ou can then convert them eihter to
latex format to view locally or to Blackboards tab-delimited format. You can
see the latex format with
```
$ python txt2bb.py --latex questions.txt
\documentclass{article}
\begin{document}
\begin{enumerate}
\item
Which of these ODEs is linear?
... (continues)
```
You can send that yo a file and compile it using
```
$ python txt2bb.py --latex questions.txt > questions.tex
$ pdflatex questions.tex
```
That will give you a questions.pdf that you can use to look at the questions.

When you are ready to upload your questions you can convert them to Blackboard
format:
```
$ python txt2bb.py --bb questions.txt > questions_bb.txt
```

Note
----

You can now upload questions_bb.txt to Blackboard as a test or question pool
using the "Upload questions" button. The latex embedded with double dollar
e.g. `$$y = x^2$$` in questions_bb.txt will not automatically render when
uploaded as rendering latex is a feature of the web editor. This means that
after uploading you have to edit each question and then save without chaging
anything to triger hte latex rendering (maybe there is a better way...).
