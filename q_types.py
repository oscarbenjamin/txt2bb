#!/usr/bin/env python3

"""
Class for each question type available on Blackboard. Fill-in, and file upload question
types are not included
"""
class Q_process:
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
    pass

class ESS(Q_process):
    pass

class ORD(Q_process):
    pass

class MAT(Q_process):
    pass

class NUM(Q_process):
    pass

class SR(Q_process):
    pass

class OP(Q_process):
    pass

class JUMBLED_SENTENCE(Q_process):
    pass

class QUIZ_BOWL(Q_process):
    pass

q_handlers = (MC, MA, TF, ESS, ORD, MAT, NUM, SR, OP, JUMBLED_SENTENCE, QUIZ_BOWL)



