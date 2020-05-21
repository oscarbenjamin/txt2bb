TXT2BB
======

A simple utility for writing questions in plain text that can be imported as
question "pools", "tests", or "surveys" in Blackboard when making online tests.
The tests can be written and viewed locally in latex before converting to
Blackboard format and uploading.


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
All questions must begin with the dashes shown in the example, they must
specify a valid type, and a prompt (the question). See the
provided questions.txt file for examples. Explanations on how each question
type is formatted can be found
[here](https://www.csustan.edu/sites/default/files/blackboard/FacultyHelp/Documents/UploadingQuestions.pdf).

### Multi Question Generating

In order to generate multiple versions of the same question, the list of
variants must be listed between `%{` and `}%`, separated by commas. These
variants can be placed within both questions and answers but there must
be the same number of variants in each list as they will be matched up when the
multiple questions are generated. An example is shown below

```
type: MC
prompt: What is the square root of %{16, 25, 36}%?
correct: %{4, 5, 6}%
incorrect: %{2, 6, 7}%
incorrect: 3
incorrect: 8
```

This will produce three similar questions, the first being:

```
type: MC
prompt: What is the square root of 16?
correct: 4
incorrect: 2
incorrect: 3
incorrect: 8
```

Be careful that the variants labelled 'correct' and 'incorrect' will definitely be accurate when
matching up with the question variant if there is one. 

If you wish to include a `,` in the option itself it should be written as `\,`
to avoid the script thinking you are separating two variants.

### NOTES:

If the question should contain a linebreak, start each new line with `>`. 

If you wish to ignore a linebreak in the input file finish the line with '\'

For example:
```
This is a line that you do not wish\
to break so must use '\'.
>This will be written as a new line since it starts with a '>'
```
will produce
```
This is a line that you do not wish to break so must begin immediately with '\'.
This will be written as a new line since it starts with a '>'
```

New lines should always either be a new entry (such as the next answer), or escaped with `\`, or enforced
with `>`.

Examples of every question can be found in questions.txt.

For question type `JUMBLED_SENTENCE`, the choices are listed as answers,
followed by any variables they correspond to. The variables appear after a
second colon and are separated by commas if multiple variables correspond to
the choice. **You cannot use `[` or `]` within this question type apart from to
specify variables**

For question types `ESS` and `SR` there is the option to add an example
answer, preceded by `example: `. 

For question type `NUM`, there is the option to add a tolerance for the answer
which is preceded by `tolerance: ` in the questions file.

For question type `MAT`, pairs must be preceded by `match_a` and `match_b`.

Usage
-----
```
$ python txt2bb.py (--latex | --bb | --all) [--randomise] in_file.txt [in_file2.txt ...] [--output out_file.txt]
```

Once you have your questions written up, you can convert them either to
latex format to view locally or to Blackboards tab-delimited format, or produce
both along with the compiled latex pdf. To produce all documents at once you
would run

```
$ python txt2bb.py --all questions.txt
```
which will produce three key files:
* `questions.tex`
* `questions.pdf`
* `questions_bb.txt`

If you wish to produce just the Latex format you can run

```
$ python txt2bb.py --latex questions.txt
```
which will produce `questions.tex`.

You can then compile that file using 
```
$ python txt2bb.py --latex questions.txt
$ pdflatex questions.tex
```
That will give you a questions.pdf that you can use to look at the questions.

You can also produce just the Blackboard format with
```
$ python txt2bb.py --bb questions.txt
```
which will produce questions_bb.txt. This is then ready to upload to
Blackboard.

Multiple question files at once can be parsed, a corresponding file for each
input file will be produced in whichever format, or if `--all` is specified
then all three file types will be produced for each input file.

The order that answers are given is preserved in this script. If you wish for
Multiple choice and Multiple answer type questions to have their answers
randomised automatically, this can be specified with the additional flag
`--randomise`. An example of how this would look when producing both Latex and
blackboard files is

```
$ python txt2bb.py --all --randomise questions.txt
```
There is also the functionality to direct the output to a specific file with
the optional flag `--output` followed by the filename you wish to direct to.
This should be added at the end of the arguments and will only work if one
input file is specified since otherwise each input file will overwrite the same
output file.

Note
----

You can now upload questions_bb.txt to Blackboard as a test or question pool
using the "Upload questions" button. The blackboard format text file will have
been compiled to run alongside MathJax. The HTML code within the file
MathJax.txt should be pasted into the 'Instructions' box of any test you are
producing with this script. When presented with the 'Instructions' box, click
the 'HTML' button in the toolbar and paste the code into there then click
update. Once this is submitted the equations should render correctly within
the browser.

