# Web interfacing utility for Blackboard

This script will provide a fast was to render LaTeX (actually MathML) code into
actual equations without needing to manually edit then save and submit the
question again.
## Dependencies:

This currently requires both Chrome and the chrome driver to allow for website
interactions.

* Google Chrome
* Chrome Webdriver found [Here](https://chromedriver.storage.googleapis.com/index.html?path=81.0.4044.69/)
* [Selenium](https://selenium-python.readthedocs.io/)


## Usage:

To run this script you will first need to have created a test in Blackboard.
[Here](https://github.com/oscarbenjamin/txt2bb "Text file upload to Blackboard")
is a repository that allows you to write the questions in a text document for
efficient upload to Blackboard, alternatively, you can create the test within
Blackboard.

Once the test is created, click its drop down menu and select 'edit test' which
will take you to the editing page in which the questions can be edited
indivually. Copy the current url of this page to your clipboard.

The file can then be run with 

```
python3 'Blackboard url' [--hide]
```

Where the blackboard url should be placed between quotations.

The optional `--hide` flag will run this script without opening an actual
Chrome browser but will require you to enter your login details into the
terminal rather than the secure login page directly.
