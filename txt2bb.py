#!/usr/bin/env python3

"""
txt2bb.py
v0.1 (2nd April 2020)
Oscar Benjamin

CLI to generate input for LaTeX or Blackboard with embedded LaTeX equations.

Usage
=====

First write a questions file.

Convert questions to LaTeX and generate PDF:

    $ ./txt2bb.py --latex myquestions.txt > myquestions.tex
    $ pdflatex myquestions.tex

Generate input file for Blackboard:

    $ ./txt2bb.py --bb myquestions.txt > myquestions_bb.txt

The file myquestions_bb.txt can now be uploaded to Blackboard using the
"Upload questions" button.

NOTE: Blackboard will not render any embedded latex automatically wen uploaded
in this way. Each question must afterwards be opened in the Blackboard editor
and saved again (without any editing) which causes the latex ot be rendered.
"""


import sys
import re
import q_types

Q_TYPES = ('MC', 'MA', 'TF', 'ESS', 'ORD', 'MAT', 'FIL', 'NUM', 'SR', 'OP',
        'JUMBLED_SENTENCE', 'QUIZ_BOWL')
IN_TYPES = ('correct', 'incorrect', 'answer', 'match_a', 'match_b', 'example',
        'tolerance', 'variable', 'q_word', 'q_phrase')        
HANDLERS = dict(zip(Q_TYPES,q_types.q_handlers))

def main(mode, filename):
    """ $ ./txt2bb.py (--latex|--b) FILE """

    with open(filename) as infile:
        questions = txt2py(mode,infile)

    if mode == "--latex":
        lines = q2latex(questions)
    else:
        lines = q2bb(questions)

    for line in lines:
        print(line)

    return 0


def txt2py(mode, infile):
    """Parse input text format into Python objects.

    list of lines (str) -> list of questions (dict)
    """

    questions = []
    if mode == "--latex":
        #format multi-lines for latex 
        text = re.sub(' *\n> *',r'\\\\',infile.read())
        lines = text.splitlines()
    elif mode == "--bb":
        #format multi-lines for bb 
        text = re.sub(' *\n> *','<br>',infile.read())
        lines = text.splitlines()
    else:
        raise ValueError("Bad mode %r" % mode)

    for lineno, line in enumerate(lines, 1):
        # Skip comments or blank lines
        if not line or line.startswith('#'):
            continue

        # Start of a new question
        elif line.startswith("-------"):
            question = {}
            questions.append(question)

        # key : val
        elif ':' in line:
            key, val = line.split(':',1)
            key = key.strip()
            val = val.strip()
            if key not in IN_TYPES + ('type', 'prompt'):
                msg = "Line %s: Unrecognised key %s" % (lineno, key)
                raise ValueError(msg)

            # some keys can be repeated so collect valuse in a list
            if key in IN_TYPES:
                if key not in question:
                    question[key] = [val]
                else:
                    question[key].append(val)
            elif key in ('type', 'prompt'):
                question[key] = val
    
    return questions


def q2bb(questions):
    """Convert multiple questions to Blackboard delimited format

    list of questions (dict) -> lines of output (str)
    """
    for question in questions:
        yield q2bb1(question)


def q2bb1(question):
    """Convert question into Blackboard tab delimited format"""
    if question["type"] in Q_TYPES:
        handler = HANDLERS[question["type"]](question)
    else:
        raise ValueError("Unrecognised question type")
    items = handler.bb()
    # Output must be tab-delimited
    # Need double-$ in Blackboard
    return "\t".join(items).replace("$", "$$")


LATEX_START = r"""
\documentclass{article}
\begin{document}
"""

LATEX_END = r"""
\end{document}
"""

ENUM_START = r"\begin{enumerate}"
ENUM_END = r"\end{enumerate}"
ITEM = r"\item"


def q2latex(questions):
    """Convert multiple questions to latex

    list of questions (dict) -> lines of output (str)

    The result is a self-contained LaTeX document
    """
    yield from LATEX_START.splitlines()
    yield from latex_enumerate(questions, q2latex1)
    yield from LATEX_END.splitlines()


def q2latex1(question):
    """Convert single question to latex

    question (dict) -> lines of output (latex)

    The result is a fragment of latex.
    """
    yield question["prompt"]
    if question["type"] in Q_TYPES:
        handler = HANDLERS[question["type"]](question)
        items = handler.latex()
        latex_item = lambda item: [r"\emph{%s}: %s" % item]
        if not items:
            pass
        #enumeration not needed if 1 element or different pairings used
        elif len(items) == 1 or question["type"] in ('ORD','MAT','JUMBLED_SENTENCE'):
            for item in items:
                yield ""
                yield from latex_item(item)
        else:
            yield from latex_enumerate(items, latex_item)
    else:
        raise ValueError("Unrecognised question type")


def latex_enumerate(items, latex_item_func):
    """Wrap items in a latex enumerate"""
    yield ENUM_START
    for item in items:
        yield ITEM
        yield from latex_item_func(item)
    yield ENUM_END


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
