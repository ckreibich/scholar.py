scholar.py
==========

scholar.py is a Python module that implements a querier and parser for Google Scholar's output. Its classes can be used independently, but it can also be invoked as a command-line tool.

The script used to live at http://icir.org/christian/scholar.html, and I've moved it here so I can more easily manage the various patches and suggestions I'm receiving for scholar.py. Thanks guys, for all your interest! If you'd like to get in touch, email me at christian@icir.org or ping me [on Twitter](http://twitter.com/ckreibich).

Cheers,<br>
Christian

Features
--------

* Extracts publication title, main online URL, number of citations, number of online versions, link to Google Scholar's main cluster for the work, and Google Scholar's cluster of all works referencing the publication.
* Prints entries in CSV format or plain text.

Example
-------

Try scholar.py --help for all available options. A simple example:

    $ scholar.py -c 1 --txt --author einstein quantum
	Title Can quantum-mechanical description of physical reality be considered complete?
        	   URL http://prola.aps.org/abstract/PR/v47/i10/p777_1
	     Citations 12088
	      Versions 160
	Citations list http://scholar.google.com/scholar?cites=8174092782678430881&as_sdt=2005&sciodt=1,5&hl=en&num=1
	 Versions list http://scholar.google.com/scholar?cluster=8174092782678430881&hl=en&num=1&as_sdt=1,5
	          Year 1935
	      PDF file http://www.df.uba.ar/users/giribet/f4/mq1.pdf



 
License
-------

scholar.py is using the standard [BSD license](http://opensource.org/licenses/BSD-2-Clause).
