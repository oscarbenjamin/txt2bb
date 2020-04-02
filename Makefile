.SECONDARY:

all: questions.done

%.done: %.pdf %_bb.txt
	touch $@

%.tex: %.txt
	./txt2latex.py --latex $< > $@

%.pdf: %.tex
	pdflatex $<

%_bb.txt: %.txt
	./txt2latex.py --bb $< > $@

clean:
	rm *.aux *.log *.pdf *_bb.txt *.done *.tex
