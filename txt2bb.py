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
import subprocess
import copy

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
        correct_occur = re.findall("[^in]correct",str([item[0] for item in self.answers]))
        if len(correct_occur) != 1:
            raise ValueError("Only 1 correct answer should be provided")

    def bb(self):
        items = [self.type, self.prompt]
        for correct, ans in self.answers:
            correct = re.findall("[a-zA-Z]+",correct)[0]   
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
            correct = re.findall("[a-zA-Z]+",correct)[0]   
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
            raise ValueError("Valid answers are true or false")
        if '(' in self.answers[0][0]:
            raise ValueError("No partial marks allowed for true or false")
        
    def bb(self):
        return [self.type, self.prompt, self.answers[0][1]]

    def latex(self):
        return [('answer', self.answers[0][1])]


class ESS(Question):
    def bb(self):
        if '(' in self.answers[0][0]:
            raise ValueError("No partial marks allowed for essay questions")

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
            raise AssertionError("Number of answers must be between 1 and 20")

        if any('(' in item[0] for item in self.answers):
            raise ValueError("No partial marks allowed for order questions")

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

        if any('(' in item[0] for item in self.answers):
            raise ValueError("No partial marks allowed for matching questions")


    def bb(self):
        return [self.type, self.prompt]+[val for _,val in self.answers]

    def latex(self):
        letter = ('a','b')
        items = [(str(num//2)+letter[num%2], ans[1]) for num, ans in
                zip(range(2,len(self.answers)+2), self.answers)]
        return items


class FIL(Question):
    def bb(self):
        if any('(' in item[0] for item in self.answers):
            raise ValueError("No partial marks allowed for this question type")
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

        if any('(' in item[0] for item in self.answers):
            raise ValueError("No partial marks allowed for number questions")

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
        if any('(' in item[0] for item in self.answers):
            raise ValueError("No partial marks allowed for jumbled sentence questions")

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
        if any('(' in item[0] for item in self.answers):
            raise ValueError("No partial marks allowed for fill in the blank questions")
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
        'tolerance', 'variable', 'q_word', 'q_phrase', 'notes')
HANDLERS = dict(zip(Q_TYPES, q_handlers))

def main(out_format, random, filename, out_file):
   
    raw_questions = txt2py(filename)
    questions = []

    for question in raw_questions:
        # Check if variants are included in the question
        if re.search('%{', str(question)):
            questions += produce_variant_questions(question)
        else:
            questions.append(question)
    
    # Randomise applicable questions if specified
    if random:
        import random
        for question in questions:
            if question['type'] in ['MA','MC','JUMBLED_SENTENCE']:
                random.shuffle(question['answers'])

    if out_format == "--latex":
        lines = q2latex(questions)
    elif out_format == "--bb":
        lines = q2bb(questions)
    with open(out_file,'w') as out:
        for line in lines:
            print(line, file=out)

    return 0

def extract_variants(question):
    # Find all options encased by %{ }%
    unboxed_question = question['answers'] + [('prompt', question['prompt'])] 
    variants = []
    for in_type, text in unboxed_question:
        text_variants = re.findall(r'%{(.*?)}%', text)
        type_variants = re.findall(r'%{(.*?)}%', in_type)
        # Split list at ',' if not escaped with \ and add to labelled list of variants
        variants.append(([re.split(r' *(?<!\\), *', item) for item in type_variants], 
                         [re.split(r' *(?<!\\), *', item) for item in text_variants]))
    
    # Check all options can be matched up (equal length option lists)
    lens = [len(i) for _,text in variants for i in text] + [len(i) for typ,_ in variants for i in typ]
    if len(set(lens)) != 1:
        raise ValueError("\n\n  All variants must be the same length\n")
    return variants, lens[0]

def produce_variant_questions(question):
    """Produce all specified variants of questions

    question (dict) -> question_variants (list[dict])
    """
    question_variants = []
    variants, num_variants = extract_variants(question)
    for i in range(num_variants):
        # Create new question using the ith entries in variant lists
        var_question = copy.deepcopy(question)
        question_variants.append(var_question)
        # Go through each item that can contain variants and switch them out
        for j, item in enumerate(var_question['answers'] + [('prompt', var_question['prompt'])]):
            # Find any variant lists in item that need to be swapped out for their ith variant 
            text_replace = re.findall('%{.*?}%', item[1])
            type_replace = re.findall('%{.*?}%', item[0])
            for k, entry in enumerate(text_replace):
                # Replace escaped , in current variant
                var = variants[j][1][k][i].replace('\,',',')
                if item[0] == 'prompt':
                    var_question['prompt'] = var_question['prompt'].replace(entry, var)
                else:
                    in_type, text = var_question['answers'][j]
                    var_question['answers'][j] = (in_type,text.replace(entry, var))
            for k, entry in enumerate(type_replace):
                # Replace escaped , in current variant
                var = variants[j][0][k][i].replace('\,',',')
                in_type, text = var_question['answers'][j]
                var_question['answers'][j] = (in_type.replace(entry, var), text)

        # Check all in_types are valid for each variant
        if any(re.findall("[a-zA-Z]+",typ)[0] not in IN_TYPES + ('type', 'prompt') for typ,_ in var_question['answers']):
            key = list(set(typ for typ,_ in var_question['answers']) - set(IN_TYPES+('type', 'prompt')))[0]
            q = var_question['prompt'][:100]+'...' if len(var_question['prompt']) > 100 else var_question['prompt']
            msg = '\n\n    Unrecognised key "{}" for question "{}"\n'.format(key,q)
            raise ValueError(msg)

    return question_variants

def error_check_raise(file_name, expr, text, msg):
    if re.search(expr, text):
        pos = re.search(expr, text).start()
        line = text[:pos].count('\n') + 1
        msg = '\n\n   '+file_name+': '+msg.format(line)+'\n'
        raise SyntaxError(msg)

def parse_checker(file_name, text):
    """Run through all known causes of errors when uploading to Blackboard and
    raise them to be fixed before any files are produced.
    """
    msg = '"<" on line {} needs a space after it.'
    error_check_raise(file_name, '<\S', text, msg)
    msg = '">" on line {} needs a space before it.'
    error_check_raise(file_name, '.\S>', text, msg)
    msg = 'Tab used on line {}. Instead use spaces.'
    error_check_raise(file_name, r'\t', text, msg)
    msg = '"\\text{{}}" used on line {}. Instead use "\\mathrm{{}}".'
    error_check_raise(file_name, r'\\text{', text, msg)
    msg = '"\\def{{}}" used in line {}. Not supported in MathJax.'
    error_check_raise(file_name, r'\\def{', text, msg)
    msg = 'Space used within "\\mathrm{{}}" on line {}. Instead use "\\,".'
    error_check_raise(file_name, r'\\mathrm{[^ }]* ', text, msg)
    msg = 'Space used in equation on line {}. Delete or replace with "{{}}" if needed.'
    eqs = re.findall(r'\$+[^\$]*\$+', text)
    for eq in eqs:
        if ' ' in eq:
            error_check_raise(file_name, re.escape(eq[eq.index(' '):]), text, msg)

def txt2py(filename):
    """Parse input text format into Python objects.

    list of lines (str) -> list of questions (dict)
    """

    questions = []
    with open(filename, 'r') as infile:
        text = infile.read()

    parse_checker(filename, text)

    # Inserting linebreak character for --bb case (<br>), this then
    # functions as placeholder for --latex case (\\)
    text = re.sub(' *\n> *','<br>', text)
    
    # This appears when using bmatrix etc. and should be flattened
    text = re.sub(r' *\\\\\n *',r'\\\\', text)
    # This flattens newlines that are escaped with '\'
    text = re.sub(r'\\\n','', text)

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

            if key in ('type', 'prompt'):
                question[key] = val
            else:
                question['answers'].append((key,val))
    
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
    # Add image pointers for uploader to replace with actual image
    for i in range(len(items)):
        items[i] = re.sub('@{(.+?)}@', r'+++FIGURE "\1" HERE+++', items[i])
    if 'notes' in items:
        del items[items.index('notes')-1:items.index('notes')+1]
    # Output must be tab-delimited, blackboard already uses $$ for its inbuilt
    # display math mode so these are changed to the MathJax configured one
    return "\t".join(items).replace("$$","~~")


LATEX_START = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
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
    typ, ans = item
    # Replaces line break symbol <br> from txt2py() and returns latex formatted line
    ans = ans.replace('<br>',r'\\')
    # Escape any % that aren't already as they comment out the line in Latex
    ans = re.sub(r'(?<!\\)%','\\%', ans)
    # Prevent answer lines from showing up in display mode
    ans = ans.replace('$$',r'$')
    # Handle partial marks
    if '(' in typ:
        par_cred = typ[typ.index('('):typ.index(')')+1]
        typ = re.findall("[a-zA-Z]+", typ)[0]
        return [r"\textbf{{{}}} - \emph{{{}}}: {}".format(par_cred, typ, ans)]

    return [r"\emph{{{}}}: {}".format(typ, ans)]

def q2latex1(question):
    """Convert single question to latex

    question (dict) -> lines of output (latex)

    The result is a fragment of latex.
    """
    # Replaces line break symbol <br> from txt2py() and returns latex formatted line
    prompt = question['prompt'].replace('<br>',r'\\\\')
    # Escape any % that aren't already as they comment out the line in Latex
    prompt = re.sub(r'(?<!\\)%','\\%', prompt)
    # Add specified images to Latex version at 0.7*textwidth
    prompt = re.sub('@{(.+?)}@',r'\\includegraphics[width=0.7\\textwidth]{\1}',prompt)
    # Add specified images to answers aswell since this is (sort of) supported aswell
    for i in range(len(question['answers'])):
        text_with_im = re.sub('@{(.+?)}@',r'\\includegraphics[width=0.7\\textwidth]{\1}', question['answers'][i][1])
        question['answers'][i] = (question['answers'][i][0], text_with_im)
               
    yield prompt
    if question['type'] in Q_TYPES:
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
            notes = ''
            if 'notes' in [item[0] for item in items]:
                notes = items.pop([item[0] for item in items].index('notes'))[1]
            yield from latex_enumerate(items, latex_item)
            if notes:  yield r"\textbf{Notes: }"+notes
    else:
        raise ValueError("Unrecognised question type")


def latex_enumerate(items, latex_item_func):
    """Wrap items in a latex enumerate"""
    yield ENUM_START
    for item in items:
        yield ITEM
        yield from latex_item_func(item)
    yield ENUM_END

def make_outfiles(out_format, random, in_files, out_file):
    for f in in_files:
        if out_format == '--bb':
            bb_file = f.strip('.txt')+'_bb.txt' if not out_file else out_file
            main(out_format, random, f, bb_file)
        
        elif out_format == '--latex':
            latex_file = f.strip('.txt')+'.tex' if not out_file else out_file
            main(out_format, random, f, latex_file)
        else:
            main('--bb', random, f, f.strip('.txt')+'_bb.txt')
            main('--latex', random, f, f.strip('.txt')+'.tex')
            subprocess.run(['pdflatex',f.strip('.txt')+'.tex'])

if __name__ == "__main__":
    out_format = sys.argv[1]
    if out_format not in ['--bb','--latex','--all']:
        raise ValueError('\n---Out format must be --bb,--latex, or --all---\n')

    random = True if sys.argv[2]=='--randomise' else False
    files = sys.argv[3:] if random else sys.argv[2:]
    out_file = None

    if '--output' in files:
        out_file = files[-1]
        files = files[:-2]
        if len(files) != 1:
            raise ValueError('\n---Only 1 input file permitted if output file specified---\n')
    
    make_outfiles(out_format, random, files, out_file)
    
