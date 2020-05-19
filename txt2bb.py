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
        self.answers = question['answers']

class MC(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        correct_occur = re.findall("'correct'",str(self.answers))

        if len(correct_occur) != 1:
            raise ValueError("Only 1 correct answer should be provided")

    def bb(self):
        items = [self.type, self.prompt]
        for correct, ans in self.answers:
                items.append(ans)
                items.append(correct)
        return items

    def latex(self):
        items = []
        for correct, ans in self.answers:
                items.append((correct, ans))
        return items


class MA(Question):
    def bb(self):
        items = [self.type, self.prompt]
        for correct, ans in self.answers:
                items.append(ans)
                items.append(correct)
        return items

    def latex(self):
        items = []
        for correct, ans in self.answers:
                items.append((correct, ans))
        return items


class TF(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        ans_occur = re.findall("'answer'",str(self.answers))
        if len(ans_occur) != 1:
            raise ValueError("Only 1 answer should be provided")
        if self.answers[0][1] not in ('true','false'):
            raise ValueError("valid answers are true or false")

    def bb(self):
        return [self.type, self.prompt, self.answers[0][1]]

    def latex(self):
        return [('answer', self.answers[0][1])]


class ESS(Question):
    def bb(self):
        if self.answers:
            return [self.type, self.prompt, self.answers[0][1]]
        else:
            return [self.type, self.prompt]

    def latex(self):
        if self.answers:
            return [('example', self.answers[0][1])]
        else:
            return None


class ORD(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        if not 1 <= len(self.answers) <= 20:
            raise AssertionError("number of answers must be between 1 and 20")

    def bb(self):
        return [self.type, self.prompt]+[ans for _,ans in self.answers]

    def latex(self):
        items = [(num, ans[1]) for num, ans in enumerate(self.answers, 1)]
        return items


class MAT(Question):
    def __init__(self, question):
        Question.__init__(self, question)
        mata = re.findall('match_a', str(self.answers))
        matb = re.findall('match_b', str(self.answers))
        if len(mata) != len(matb):
            raise AssertionError("All options must have matching answers")

    def bb(self):
        return [self.type, self.prompt]+[val for _,val in self.answers]

    def latex(self):
        letter = ('a','b')
        items = [(str(num//2)+letter[num%2], ans[1]) for num, ans in
                zip(range(2,len(self.answers)+2), self.answers)]
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
            self.ans = str(float(self.answers[0][1]))
            if 'tolerance' in str(self.answers):
                self.tol = str(float(self.answers[1][1]))
        except:
            raise ValueError('answer and tolerance must be numbers')

    def bb(self):
        if 'tolerance' in str(self.answers):
            return [self.type, self.prompt, self.ans, self.tol]
        else:
            return [self.type, self.prompt, self.ans]

    def latex(self):
        if 'tolerance' in str(self.answers):
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
        self.mappings = {}
        var_list = []
        answers = [ans for _,ans in self.answers]
        for ans in answers:
            # Check if variable(s) have been linked to the choice
            if re.search(r':.*\w',ans):
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
                choice, var = ans.strip(':'), None

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


class FIB_PLUS(Question):
    # Fill in the blank (multiple blanks)
    def __init__(self, question):
        Question.__init__(self, question)
        answers = [ans for _,ans in self.answers]
        self.mappings = {}
        ans_list = []
        for ans in answers:
            # Check variable has been linked to the choice
            if re.search(r':.*\w',ans):
                variable, answers = map(str.strip,ans.split(':'))
                # Check if multiple variables (separated by commas) are present
                if re.search(r'(?<!\\),',answers):
                    # Split at commas if not escaped with \
                    ans = list(map(str.strip, answers.split(',')))
                    ans_list += ans
                else:
                    # Otherwise save the single variable (removing any escape slashes)
                    ans = answers.replace('\\','')
                    ans_list.append(ans)

                self.mappings[variable] = ans
            else:
                raise ValueError('Variable is not given answers')
    def bb(self):
        items = [self.type, self.prompt]
        for var, ans in self.mappings.items():
            items.append(var)
            if type(ans) == list:
                items += ans
            else:
                items.append(ans)
            items.append('')
        return items

    def latex(self):
        items = []
        for var, ans in self.mappings.items():
            if type(ans) == list:
                items.append((var, ', '.join(ans)))
            else:
                items.append((var,str(ans)))
        return items

# Tuple of all classes for use in dictionary in txt2bb
q_handlers = (MC, MA, TF, ESS, ORD, MAT, FIL, NUM, SR, OP, JUMBLED_SENTENCE, FIB_PLUS)


#-----------------------------------File Handling-------------------------------------#
Q_TYPES = ('MC', 'MA', 'TF', 'ESS', 'ORD', 'MAT', 'FIL', 'NUM', 'SR', 'OP',
        'JUMBLED_SENTENCE', 'FIB_PLUS')
IN_TYPES = ('correct', 'incorrect', 'answer', 'match_a', 'match_b', 'example',
        'tolerance', 'variable', 'q_word', 'q_phrase')
HANDLERS = dict(zip(Q_TYPES, q_handlers))

def main(mode, filename, random='no'):
    """ $ ./txt2bb.py (--latex|--bb) FILE [--randomise]"""
   
    with open(filename) as infile:
        raw_questions = txt2py(infile)
    
    questions = []

    for question in raw_questions:
        # Check if variants are included in the question
        if re.search('%{', str(question)):
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
                            var_question[key] = [item.replace(entry, variant) for item in var_question[key]]
                        else:
                            var_question[key] = var_question[key].replace(entry, variant)
        else:
            questions.append(question)
    
    # Randomise applicable questions if specified
    random = True if random.lower() in ['--r','--randomise'] else False
    if random:
        import random
        for question in questions:
            if question['type'] in ['MA','MC']:
                random.shuffle(question['answers'])


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
    variants_dict = {}
    for key, val in question.items():
        variants = re.findall(r'%{(.*?)}%', ''.join(chain.from_iterable(val)))
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
    # Mathjax cannot have > or < next to a letter (space needed) ignore <br>
    text = re.sub(' *(?<!br)(<|>)(?!br) *', r' \1 ', text)
    # Remove tabs to avoid confusing bb format
    text = re.sub('\t', '', text)
    # This appears when using bmatrix etc. and should be flattened
    text = re.sub(r' *\\\\\n *',r'\\\\', text)
    # This flattens newlines that are escaped with '\'
    text = re.sub(r' *\\\n *',' ', text)
    # Replace all space in equations with {} to avoid Blackboard messing up
    # Replace all space within \text or \mathrm with \', instead of {}
    text = text.replace('\\text{','\\mathrm{')
    eq_texts = re.findall(r'\\mathrm({.*?})', text)
    for eq_text in eq_texts:
        text = text.replace(eq_text, re.sub(' ','\\,', eq_text))

    # Cannot have space after \left or \right as {} will be inserted after
    text = re.sub(r'(\\left|\\right) +',r'\1', text)
    # Should not have spaces between commands such as \begin{array} {l} or {l} \hline
    text = re.sub(r'} +{', r'}{', text)
    text = re.sub(r'} +\\', r'}\\', text)
    text = re.sub(r'(\\\w*)? +\\', r'\1\\', text)

    eqs = re.findall('\$+([^\$]+?)\$+', text)
    for eq in eqs:
        text = text.replace(eq,re.sub(' ','{}',eq))
        
    lines = text.splitlines()

    for lineno, line in enumerate(lines, 1):
        # Skip comments or blank lines
        if not line or line.startswith('#'):
            continue

        # Start of a new question
        elif line.startswith("-------"):
            question = {}
            question['answers'] = []
            questions.append(question)

        # key : val
        elif ':' in line:
            key, val = line.split(':',1)
            key = key.strip()
            val = val.strip()
            if key not in IN_TYPES + ('type', 'prompt'):
                msg = "Line %s: Unrecognised key %s" % (lineno, key)
                raise ValueError(msg)

            if key in IN_TYPES:
                question['answers'].append((key,val))
            else:
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
    # Add Separating new line after question to avoid overcrowded look
    items[1]+='<p></p>'
    # Output must be tab-delimited, blackboard already uses $$ for its inbuilt
    # display math mode so these are changed to the MathJax configured one
    return "\t".join(items).replace("$$","~~")


LATEX_START = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amssymb}
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
    # Escape any % that aren't already as they comment out the line in Latex
    item = (item[0],re.sub(r'(?<!\\)%','\\%', item[1]))
    # Prevent answer lines from showing up in display mode
    item = (item[0],item[1].replace('$$',r'$'))
    return [r"\emph{%s}: %s" % item]

def q2latex1(question):
    """Convert single question to latex

    question (dict) -> lines of output (latex)

    The result is a fragment of latex.
    """
    # Replaces line break symbol <br> from txt2py() and returns latex formatted line
    prompt = question["prompt"].replace('<br>',r'\\\\')
    # Escape any % that aren't already as they comment out the line in Latex
    prompt = re.sub(r'(?<!\\)%','\\%', prompt)
    yield prompt
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


