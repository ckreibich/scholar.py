# ChangeLog
# ---------
#
# 2.11  The Scholar site seems to have become more picky about the
#       number of results requested. The default of 20 in scholar.py
#       could cause HTTP 503 responses. scholar.py now doesn't request
#       a maximum unless you provide it at the comment line. (For the
#       time being, you still cannot request more than 20 results.)
#
# 2.10  Merged a fix for the "TypError: quote_from_bytes()" problem on
#       Python 3.x from hinnefe2.
#
# 2.9   Fixed Unicode problem in certain queries. Thanks to smidm for
#       this contribution.
#
# 2.8   Improved quotation-mark handling for multi-word phrases in
#       queries. Also, log URLs %-decoded in debugging output, for
#       easier interpretation.
#
# 2.7   Ability to extract content excerpts as reported in search results.
#       Also a fix to -s|--some and -n|--none: these did not yet support
#       passing lists of phrases. This now works correctly if you provide
#       separate phrases via commas.
#
# 2.6   Ability to disable inclusion of patents and citations. This
#       has the same effect as unchecking the two patents/citations
#       checkboxes in the Scholar UI, which are checked by default.
#       Accordingly, the command-line options are --no-patents and
#       --no-citations.
#
# 2.5:  Ability to parse global result attributes. This right now means
#       only the total number of results as reported by Scholar at the
#       top of the results pages (e.g. "About 31 results"). Such
#       global result attributes end up in the new attrs member of the
#       used ScholarQuery class. To render those attributes, you need
#       to use the new --txt-globals flag.
