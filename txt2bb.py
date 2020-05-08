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
Class for each question type available on Blackboard. Fill-in and quizbowl question
types are not included

Each class corresponds to one of Blackboard's question types, for example, MC
is multiple choice. Full documentation for each question type can be found here:

https://help.blackboard.com/Learn/Instructor/Tests_Pools_Surveys/Question_Types

The way in which these questions are formatted and named can be found here:

https://www.csustan.edu/sites/default/files/blackboard/FacultyHelp/Documents/UploadingQuestions.pdf

Each class contains functions bb() and latex(), invoked by the command line
argument --bb or --latex. These functions format the question (dict) into the
appropriate (list) format for the specified file type.
"""
import sys
import re
from itertools import chain

#--------------------------------Question Classes---------------------------------#
class Question:
    """Defualt initialisation for all question handling classes
    
    questions (dict) -> assigns generic values to object
    """

    def __init__(self, question):
        self.question = question
        self.type = question['type']
        self.prompt = question['prompt']


class MC(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        if len(question['correct'])!=1:
            raise ValueError("Only 1 correct answer should be provided")

    def bb(self):
        items = [self.type, self.prompt]
        for correct in ("correct", "incorrect"):
            for ans in self.question[correct]:
                items.append(ans)
                items.append(correct)
        return items

    def latex(self):
        items = []
        for correct in ("correct", "incorrect"):
            for ans in self.question[correct]:
                items.append((correct, ans))
        return items


class MA(Question):
    def bb(self):
        items = [self.type, self.prompt]
        for correct in ("correct", "incorrect"):
            for ans in self.question[correct]:
                items.append(ans)
                items.append(correct)
        return items

    def latex(self):
        items = []
        for correct in ("correct", "incorrect"):
            for ans in self.question[correct]:
                items.append((correct, ans))
        return items


class TF(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        if len(question['answer'])!=1:
            raise ValueError("Only 1 answer should be provided")
        if question['answer'][0] not in ('true','false'):
            raise ValueError("valid answers are true or false")

    def bb(self):
        return [self.type, self.prompt, self.question['answer'][0]]

    def latex(self):
        return [('answer', self.question['answer'][0])]


class ESS(Question):
    def bb(self):
        if 'example' in self.question.keys():
            return [self.type, self.prompt, self.question['example'][0]]
        else:
            return [self.type, self.prompt]

    def latex(self):
        if 'example' in self.question.keys():
            return [('example', self.question['example'][0])]
        else:
            return None


class ORD(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        if not 1 <= len(question['answer']) <= 20:
            raise AssertionError("number of answers must be between 1 and 20")

    def bb(self):
        return [self.type, self.prompt, *self.question['answer']]

    def latex(self):
        items = [(num, ans) for num, ans in enumerate(self.question['answer'],1)]
        return items


class MAT(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        if len(question['match_a']) != len(question['match_b']):
            raise AssertionError("All options must have matching answers")
        a, b = question['match_a'], question['match_b']
        self.merged_pairs = [sub[item] for item in range(len(b)) for sub in [a, b]]

    def bb(self):
        return [self.type, self.prompt, *self.merged_pairs]

    def latex(self):
        letter = ('a','b')
        items = [(str(num//2)+letter[num%2], ans) for num, ans in
                zip(range(2,len(self.merged_pairs)+2), self.merged_pairs)]
        return items


class FIL(Question):
    def bb(self):
        return [self.type, self.prompt]

    def latex(self):
        return None


class NUM(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        try:
            float(question['answer'][0])
            self.ans = question['answer'][0]
            if 'tolerance' in question.keys():
                float(question['tolerance'][0])
                self.tol = question['tolerance'][0]
        except:
            raise ValueError('answer and tolerance must be numbers')
        
    def bb(self):
        if 'tolerance' in self.question.keys():
            return [self.type, self.prompt, self.ans, self.tol]
        else:
            return [self.type, self.prompt, self.ans]

    def latex(self):
        if 'tolerance' in self.question.keys():
            return [('answer', self.ans), ('tolerance', r'$\pm$'+self.tol)]
        else:
            return [('answer', self.ans)]


class SR(ESS):
    # Inherits functions form essay question class as they are identical
    pass
        

class OP(FIL):
    # Inherits functions form file upload question class as they are identical
    pass


class JUMBLED_SENTENCE(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        answers = self.question['answer']
        self.mappings = {}
        var_list = []
        for ans in answers:
            # Check if variable(s) have been linked to the choice
            if re.search(r':.\w',ans):
                choice, variables = map(str.strip,ans.split(':'))
                # Check if multiple variables (separated by commas) are present
                if re.search(r'(?<!\\),',variables):
                    # Split at commas if not escaped with \
                    var = list(map(str.strip, variables.split(',')))
                    var_list += var
                else:
                    # Otherwise save the single variable (removing any escape slashes)
                    var = variables.replace('\\','')
                    var_list.append(var)
            else:
                choice, var = ans, None

            self.mappings[choice] = var

        if any(' ' in var for var in var_list):
            raise ValueError('no space are allowed in variable names')
        if not all(var in self.prompt for var in var_list):
            raise ValueError('missing variables from prompt')
        if not (self.prompt.count('[') == self.prompt.count(']') == len(var_list)):
            raise ValueError("""incorrect number of brackets in prompt\n
            ---Make sure "[" or "]" do not appear apart from around variables---\n""")

    def bb(self):
        items = [self.type, self.prompt]
        for choice, var in self.mappings.items():
            items.append(choice)
            if type(var) == list:
                items += var
            elif var is None:
                pass
            else:
                items.append(var)
            items.append('')
        return items

    def latex(self):
        items = []
        for choice, var in self.mappings.items():
            if type(var) == list:
                items.append((choice, ', '.join(var)))
            else:
                items.append((choice,str(var)))
        return items


class QUIZ_BOWL(Question):
    # Ignored for now, most likely not needed
    def bb(self):
        pass

    def latex(self):
        pass

# Tuple of all classes for use in dictionary in txt2bb 
q_handlers = (MC, MA, TF, ESS, ORD, MAT, FIL, NUM, SR, OP, JUMBLED_SENTENCE, QUIZ_BOWL)


#-----------------------------------File Handling-------------------------------------#

Q_TYPES = ('MC', 'MA', 'TF', 'ESS', 'ORD', 'MAT', 'FIL', 'NUM', 'SR', 'OP',
        'JUMBLED_SENTENCE', 'QUIZ_BOWL')
IN_TYPES = ('correct', 'incorrect', 'answer', 'match_a', 'match_b', 'example',
        'tolerance', 'variable', 'q_word', 'q_phrase')        
HANDLERS = dict(zip(Q_TYPES, q_handlers))

def main(mode, filename):
    """ $ ./txt2bb.py (--latex|--b) FILE """

    with open(filename) as infile:
        raw_questions = txt2py(infile)
                   
    questions = []

    for question in raw_questions:
        flat_question = ''.join(chain.from_iterable(question.values()))
        # Check if variants are included in the question
        if re.search('%{', flat_question):
            variants_dict, num_variants = variant_questions(question)
            for i in range(num_variants):
                # Create new question using the ith entries in variant lists
                var_question = {}
                questions.append(var_question)
                for key, val in variants_dict.items():
                    var_question[key] = question[key]
                    to_replace = re.findall('%{.*?}%', ''.join(chain.from_iterable(question[key])))
                    for num, entry in enumerate(to_replace):
                        # Correct for escaped ',' in variant list text
                        variant = val[num][i].replace('\,',',')
                        if type(var_question[key]) == list:
                            var_question[key] = [item.replace(entry, variant) for item in question[key]]
                        else:
                            var_question[key] = var_question[key].replace(entry, variant)
        else:
            questions.append(question)


    if mode == "--latex":
        lines = q2latex(questions)
    elif mode == "--bb":
        lines = q2bb(questions)
    else:
        raise ValueError("Bad mode %r" % mode)

    for line in lines:
        print(line)

    return 0

def variant_questions(question):
    # Find all options encased by %{ }% 
    #flat_question = ''.join(chain.from_iterable(question.values()))
    variants_dict = {}
    for key, val in question.items():
        flat_val = ''.join(chain.from_iterable(val))
        variants = re.findall(r'%{(.*?)}%', flat_val)
        # Split list at ',' if not escaped with \
        variants_dict[key] = [re.split(r' *(?<!\\), *', item) for item in variants]
    # Check all options can be matched up (equal length option lists)
    lens = [len(item) for item in chain.from_iterable(variants_dict.values())]
    if len(set(lens)) != 1:
        raise ValueError("\n\n    All variants must be the same length\n")

    return variants_dict, lens[0]



def txt2py(infile):
    """Parse input text format into Python objects.

    list of lines (str) -> list of questions (dict)
    """

    questions = []
    # Inserting linebreak character for --bb case (<br>), this then 
    # functions as placeholder for --latex case (\\) 
    text = re.sub(' *\n> *','<br>',infile.read())
    # This appears when using bmatrix etc. and should be flattened
    text = re.sub(r' *\\\\\n *',r'\\\\', text)
    # This flattens newlines that are escaped with '\'
    text = re.sub(r' *\\\n *',' ', text)
    lines = text.splitlines()
    
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
\usepackage{amsmath}
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

def latex_item(item):
    # Replaces line break symbol <br> from txt2py() and returns latex formatted line
    item = (item[0],item[1].replace('<br>',r'\\'))
    return [r"\emph{%s}: %s" % item]

def q2latex1(question):
    """Convert single question to latex

    question (dict) -> lines of output (latex)

    The result is a fragment of latex.
    """
    
    yield question["prompt"].replace('<br>',r'\\\\')
    if question["type"] in Q_TYPES:
        handler = HANDLERS[question["type"]](question)
        items = handler.latex()
        if not items:
            pass
        # Enumeration not needed if 1 element or different pairings used
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

