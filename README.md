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
             Title Physics and reality
               URL http://www.sciencedirect.com/science/article/pii/S0016003236910475
         Citations 322
          Versions 5
    Citations list http://scholar.google.com/scholar?cites=6799563874330167610&as_sdt=2005&sciodt=1,5&hl=en
     Versions list http://scholar.google.com/scholar?cluster=6799563874330167610&hl=en&as_sdt=1,5&as_subj=eng
 
License
-------

scholar.py is using the standard [BSD license](http://opensource.org/licenses/BSD-2-Clause).
