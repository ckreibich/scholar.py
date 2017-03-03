ChangeLog
---------

2.11  The Scholar site seems to have become more picky about the
      number of results requested. The default of 20 in scholar.py
      could cause HTTP 503 responses. scholar.py now doesn't request
      a maximum unless you provide it at the comment line. (For the
      time being, you still cannot request more than 20 results.)

2.10  Merged a fix for the "TypError: quote_from_bytes()" problem on
      Python 3.x from hinnefe2.

2.9   Fixed Unicode problem in certain queries. Thanks to smidm for
      this contribution.

2.8   Improved quotation-mark handling for multi-word phrases in
      queries. Also, log URLs %-decoded in debugging output, for
      easier interpretation.

2.7   Ability to extract content excerpts as reported in search results.
      Also a fix to -s|--some and -n|--none: these did not yet support
      passing lists of phrases. This now works correctly if you provide
      separate phrases via commas.

2.6   Ability to disable inclusion of patents and citations. This
      has the same effect as unchecking the two patents/citations
      checkboxes in the Scholar UI, which are checked by default.
      Accordingly, the command-line options are --no-patents and
      --no-citations.

2.5:  Ability to parse global result attributes. This right now means
      only the total number of results as reported by Scholar at the
      top of the results pages (e.g. "About 31 results"). Such
      global result attributes end up in the new attrs member of the
      used ScholarQuery class. To render those attributes, you need
      to use the new --txt-globals flag.

      Rendering global results is currently not supported for CSV
      (as they don't fit the one-line-per-article pattern). For
      grepping, you can separate the global results from the
      per-article ones by looking for a line prefix of "[G]":

      $ scholar.py --txt-globals -a "Einstein"
      [G]    Results 11900

               Title Can quantum-mechanical description of physical reality be considered complete?
                 URL http://journals.aps.org/pr/abstract/10.1103/PhysRev.47.777
                Year 1935
           Citations 12804
            Versions 80
             Cluster ID 8174092782678430881
      Citations list http://scholar.google.com/scholar?cites=8174092782678430881&as_sdt=2005&sciodt=0,5&hl=en
       Versions list http://scholar.google.com/scholar?cluster=8174092782678430881&hl=en&as_sdt=0,5

2.4:  Bugfixes:

      - Correctly handle Unicode characters when reporting results
        in text format.

      - Correctly parse citation-only (i.e. linkless) results in
        Google Scholar results.

2.3:  Additional features:

      - Direct extraction of first PDF version of an article

      - Ability to pull up an article cluster's results directly.

      This is based on work from @aliparsai on GitHub -- thanks!

      - Suppress missing search results (so far shown as "None" in
        the textual output form.

2.2:  Added a logging option that reports full HTML contents, for
      debugging, as well as incrementally more detailed logging via
      -d up to -dddd.
