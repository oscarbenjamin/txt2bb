#!/usr/bin/env python3

"""
Class for each question type available on Blackboard. Fill-in question
types are not included
"""
import re

class Q_process:
    """Defualt initialisation for all question handling classes
    
    questions (dict) -> assigns generic values to object
    """

    def __init__(self, question):
        self.question = question
        self.type = question['type']
        self.prompt = question['prompt']

class MC(Q_process):
    def __init__(self, question):
        Q_process.__init__(self, question)
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

class MA(Q_process):
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

class TF(Q_process):
    def __init__(self, question):
        Q_process.__init__(self, question)
        if len(question['answer'])!=1:
            raise ValueError("Only 1 answer should be provided")
        if question['answer'][0] not in ('true','false'):
            raise ValueError("valid answers are true or false")

    def bb(self):
        return [self.type, self.prompt, self.question['answer'][0]]

    def latex(self):
        return [('answer', self.question['answer'][0])]

class ESS(Q_process):
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

class ORD(Q_process):
    def __init__(self, question):
        Q_process.__init__(self, question)
        if not 1 <= len(question['answer']) <= 20:
            raise AssertionError("number of answers must be between 1 and 20")

    def bb(self):
        return [self.type, self.prompt, *self.question['answer']]

    def latex(self):
        items = [(num, ans) for num, ans in enumerate(self.question['answer'],1)]
        return items

class MAT(Q_process):
    def __init__(self, question):
        Q_process.__init__(self, question)
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

class FIL(Q_process):
    def bb(self):
        return [self.type, self.prompt]

    def latex(self):
        return None

class NUM(Q_process):
    def __init__(self, question):
        Q_process.__init__(self, question)
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
    """Inherets functions form essay question class as they are identical"""
    pass
        
class OP(FIL):
    """Inherets functions form file upload question class as they are identical"""
    pass

class JUMBLED_SENTENCE(Q_process):
    def __init__(self, question):
        Q_process.__init__(self, question)
        answers = self.question['answer']
        self.mappings = {}
        var_list = []
        for ans in answers:
            #check if variable(s) have been linked to the choice
            if ':' in ans:
                choice, variables = map(str.strip,ans.split(':'))
                #check if multiple variables (separated by commas) are present
                if re.search(r'(?<!\\),',variables):
                    #split at commas if not escaped with \
                    var = list(map(str.strip, variables.split(',')))
                    var_list += var
                else:
                    #otherwise save the single variable (removing any escape slashes)
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
            raise ValueError('missing brackets in prompt')

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

class QUIZ_BOWL(Q_process):
    def bb(self):
        pass

    def latex(self):
        pass

#tuple of all classes for use in dictionary in txt2bb 
q_handlers = (MC, MA, TF, ESS, ORD, MAT, FIL, NUM, SR, OP, JUMBLED_SENTENCE, QUIZ_BOWL)



