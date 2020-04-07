.SECONDARY:

all: questions.done

%.done: %.pdf %_bb.txt txt2bb.py
	touch $@

%.tex: %.txt
	./txt2bb.py --latex $< > $@

%.pdf: %.tex
	pdflatex $<

%_bb.txt: %.txt
	./txt2bb.py --bb $< > $@

clean:
	rm *.aux *.log *.pdf *_bb.txt *.done *.tex
