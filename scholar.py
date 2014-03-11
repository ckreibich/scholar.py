#! /usr/bin/env python
"""
This module provides classes for querying Google Scholar and parsing
returned results. It currently *only* processes the first results
page. It is not a recursive crawler.
"""
# ChangeLog
# ---------
#
# 2.1:  Additional features:
#
#       - Improved cookie support: the new --cookie-file options
#         allows the reuse of a cookie across invocations of the tool;
#         this allows higher query rates than would otherwise result
#         when invoking scholar.py repeatedly.
#
#       - Workaround: remove the num= URL-encoded argument from parsed
#         URLs. For some reason, Google Scholar decides to propagate
#         the value from the original query into the URLs embedded in
#         the results.
#
# 2.0:  Thorough overhaul of design, with substantial improvements:
#
#       - Full support for advanced search arguments provided by
#         Google Scholar
#
#       - Support for retrieval of external citation formats, such as
#         BibTeX or EndNote
#
#       - Simple logging framework to track activity during execution
#
# 1.7:  Python 3 and BeautifulSoup 4 compatibility, as well as printing
#       of usage info when no options are given. Thanks to Pablo
#       Oliveira (https://github.com/pablooliveira)!
#
#       Also a bunch of pylinting and code cleanups.
#
# 1.6:  Cookie support, from Matej Smid (https://github.com/palmstrom).
#
# 1.5:  A few changes:
#
#       - Tweak suggested by Tobias Isenberg: use unicode during CSV
#         formatting.
#
#       - The option -c|--count now understands numbers up to 100 as
#         well. Likewise suggested by Tobias.
#
#       - By default, text rendering mode is now active. This avoids
#         confusion when playing with the script, as it used to report
#         nothing when the user didn't select an explicit output mode.
#
# 1.4:  Updates to reflect changes in Scholar's page rendering,
#       contributed by Amanda Hay at Tufts -- thanks!
#
# 1.3:  Updates to reflect changes in Scholar's page rendering.
#
# 1.2:  Minor tweaks, mostly thanks to helpful feedback from Dan Bolser.
#       Thanks Dan!
#
# 1.1:  Made author field explicit, added --author option.
#
# Don't complain about missing docstrings: pylint: disable-msg=C0111
#
# Copyright 2010--2014 Christian Kreibich. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import optparse
import os
import sys
import re

try:
    # Try importing for Python 3
    # pylint: disable-msg=F0401
    # pylint: disable-msg=E0611
    from urllib.request import HTTPCookieProcessor, Request, build_opener
    from urllib.parse import quote
    from http.cookiejar import MozillaCookieJar
except ImportError:
    # Fallback for Python 2
    from urllib2 import Request, build_opener, HTTPCookieProcessor
    from urllib import quote
    from cookielib import MozillaCookieJar

# Import BeautifulSoup -- try 4 first, fall back to older
try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup
    except ImportError:
        print('We need BeautifulSoup, sorry...')
        sys.exit(1)

# Support unicode in both Python 2 and 3. In Python 3, unicode is str.
if sys.version_info[0] == 3:
    unicode = str # pylint: disable-msg=W0622
    encode = lambda s: s # pylint: disable-msg=C0103
else:
    encode = lambda s: s.encode('utf-8') # pylint: disable-msg=C0103


class Error(Exception):
    """Base class for any Scholar error."""


class FormatError(Error):
    """A query argument or setting was formatted incorrectly."""


class ScholarConf(object):
    """Helper class for global settings."""

    VERSION = '2.0'
    LOG_LEVEL = 1
    MAX_PAGE_RESULTS = 20 # Current maximum for per-page results
    SCHOLAR_SITE = 'http://scholar.google.com'

    # USER_AGENT = 'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.2.9) Gecko/20100913 Firefox/3.6.9'
    # Let's update at this point (3/14):
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0'

    # If set, we will use this file to read/save cookies to enable
    # cookie use across sessions.
    COOKIE_JAR_FILE = None

class ScholarUtils(object):
    """A wrapper for various utensils that come in handy."""

    LOG_LEVELS = { 'error': 1,
                   'warn':  2,
                   'debug': 3 }

    @staticmethod
    def ensure_int(arg, msg=None):
        try:
            return int(arg)
        except ValueError:
            raise FormatError(msg)

    @staticmethod
    def log(level, msg):
        if level not in ScholarUtils.LOG_LEVELS.keys():
            return
        if ScholarUtils.LOG_LEVELS[level] > ScholarConf.LOG_LEVEL:
            return
        sys.stderr.write('[%5s]  %s' % (level.upper(), msg + '\n'))
        sys.stderr.flush()


class ScholarArticle(object):
    """
    A class representing articles listed on Google Scholar.  The class
    provides basic dictionary-like behavior.
    """
    def __init__(self):
        self.attrs = {
            'title':         [None, 'Title',          0],
            'url':           [None, 'URL',            1],
            'num_citations': [0,    'Citations',      2],
            'num_versions':  [0,    'Versions',       3],
            'url_citations': [None, 'Citations list', 4],
            'url_versions':  [None, 'Versions list',  5],
            'year':          [None, 'Year',           6],
            'citlink':       [None, 'Citation link',  7],
        }

        # The citation data in one of the standard export formats,
        # e.g. BibTeX.
        self.citation_data = None

    def __getitem__(self, key):
        if key in self.attrs:
            return self.attrs[key][0]
        return None

    def __len__(self):
        return len(self.attrs)

    def __setitem__(self, key, item):
        if key in self.attrs:
            self.attrs[key][0] = item
        else:
            self.attrs[key] = [item, key, len(self.attrs)]            

    def __delitem__(self, key):
        if key in self.attrs:
            del self.attrs[key]

    def set_citation_data(self, citation_data):
        self.citation_data = citation_data

    def as_txt(self):
        # Get items sorted in specified order:
        items = sorted(list(self.attrs.values()), key=lambda item: item[2])
        # Find largest label length:
        max_label_len = max([len(str(item[1])) for item in items])
        fmt = '%%%ds %%s' % max_label_len
        return '\n'.join([fmt % (item[1], item[0]) for item in items])

    def as_csv(self, header=False, sep='|'):
        # Get keys sorted in specified order:
        keys = [pair[0] for pair in \
                sorted([(key, val[2]) for key, val in list(self.attrs.items())],
                       key=lambda pair: pair[1])]
        res = []
        if header:
            res.append(sep.join(keys))
        res.append(sep.join([unicode(self.attrs[key][0]) for key in keys]))
        return '\n'.join(res)

    def as_citation(self):
        """
        Reports the article in a standard citation format. This works only
        if you have configured the querier to retrieve a particular
        citation export format. (See ScholarSettings.)
        """
        return self.citation_data or ''


class ScholarArticleParser(object):
    """
    ScholarArticleParser can parse HTML document strings obtained from
    Google Scholar. This is a base class; concrete implementations
    adapting to tweaks made by Google over time follow below.
    """
    def __init__(self, site=None):
        self.soup = None
        self.article = None
        self.site = site or ScholarConf.SCHOLAR_SITE
        self.year_re = re.compile(r'\b(?:20|19)\d{2}\b')

    def handle_article(self, art):
        """
        The parser invokes this callback on each article parsed
        successfully.  In this base class, the callback does nothing.
        """

    def parse(self, html):
        """
        This method initiates parsing of HTML content.
        """
        self.soup = BeautifulSoup(html)
        for div in self.soup.findAll(ScholarArticleParser._tag_checker):
            self._parse_article(div)

    def _parse_article(self, div):
        self.article = ScholarArticle()

        for tag in div:
            if not hasattr(tag, 'name'):
                continue

            if tag.name == 'div' and self._tag_has_class(tag, 'gs_rt') and \
                    tag.h3 and tag.h3.a:
                self.article['title'] = ''.join(tag.h3.a.findAll(text=True))
                self.article['url'] = self._path2url(tag.h3.a['href'])

            if tag.name == 'font':
                for tag2 in tag:
                    if not hasattr(tag2, 'name'):
                        continue
                    if tag2.name == 'span' and \
                       self._tag_has_class(tag2, 'gs_fl'):
                        self._parse_links(tag2)

        if self.article['title']:
            self.handle_article(self.article)

    def _parse_links(self, span):
        for tag in span:
            if not hasattr(tag, 'name'):
                continue
            if tag.name != 'a' or tag.get('href') == None:
                continue

            if tag.get('href').startswith('/scholar?cites'):
                if hasattr(tag, 'string') and tag.string.startswith('Cited by'):
                    self.article['num_citations'] = \
                        self._as_int(tag.string.split()[-1])

                # Weird Google Scholar behavior here: if the original
                # search query came with a number-of-results limit,
                # then this limit gets propagated to the URLs embedded
                # in the results page as well. Same applies to
                # versions URL in next if-block.
                self.article['url_citations'] = \
                    self._strip_url_arg('num', self._path2url(tag.get('href')))

            if tag.get('href').startswith('/scholar?cluster'):
                if hasattr(tag, 'string') and tag.string.startswith('All '):
                    self.article['num_versions'] = \
                        self._as_int(tag.string.split()[1])
                self.article['url_versions'] = \
                    self._strip_url_arg('num', self._path2url(tag.get('href')))

            if tag.getText().startswith('Import'):
                self.article['citlink'] = self._path2url(tag.get('href'))

    @staticmethod
    def _tag_has_class(tag, klass):
        """
        This predicate function checks whether a BeatifulSoup Tag instance
        has a class attribute.
        """
        res = tag.get('class') or []
        if type(res) != list:
            # BeautifulSoup 3 can return e.g. 'gs_md_wp gs_ttss',
            # so split -- conveniently produces a list in any case
            res = res.split()
        return klass in res

    @staticmethod
    def _tag_checker(tag):
        return tag.name == 'div' \
            and ScholarArticleParser._tag_has_class(tag, 'gs_r')

    @staticmethod
    def _as_int(obj):
        try:
            return int(obj)
        except ValueError:
            return None

    def _path2url(self, path):
        """Helper, returns full URL in case path isn't one."""
        if path.startswith('http://'):
            return path
        if not path.startswith('/'):
            path = '/' + path
        return self.site + path

    def _strip_url_arg(self, arg, url):
        """Helper, removes a URL-encoded argument, if present."""
        parts = url.split('?', 1)
        if len(parts) != 2:
            return url
        res = []
        for part in parts[1].split('&'):
            if not part.startswith(arg + '='):
                res.append(part)
        return parts[0] + '?' + '&'.join(res)


class ScholarArticleParser120201(ScholarArticleParser):
    """
    This class reflects update to the Scholar results page layout that
    Google recently.
    """
    def _parse_article(self, div):
        self.article = ScholarArticle()

        for tag in div:
            if not hasattr(tag, 'name'):
                continue

            if tag.name == 'h3' and self._tag_has_class(tag, 'gs_rt') and tag.a:
                self.article['title'] = ''.join(tag.a.findAll(text=True))
                self.article['url'] = self._path2url(tag.a['href'])

            if tag.name == 'div' and self._tag_has_class(tag, 'gs_a'):
                year = self.year_re.findall(tag.text)
                self.article['year'] = year[0] if len(year) > 0 else None

            if tag.name == 'div' and self._tag_has_class(tag, 'gs_fl'):
                self._parse_links(tag)

        if self.article['title']:
            self.handle_article(self.article)


class ScholarArticleParser120726(ScholarArticleParser):
    """
    This class reflects update to the Scholar results page layout that
    Google made 07/26/12.
    """
    def _parse_article(self, div):
        self.article = ScholarArticle()

        for tag in div:
            if not hasattr(tag, 'name'):
                continue
            if tag.name == 'div' and self._tag_has_class(tag, 'gs_ri'):
                if tag.a:
                    self.article['title'] = ''.join(tag.a.findAll(text=True))
                    self.article['url'] = self._path2url(tag.a['href'])

                if tag.find('div', {'class': 'gs_a'}):
                    year = self.year_re.findall(tag.find('div', {'class': 'gs_a'}).text)
                    self.article['year'] = year[0] if len(year) > 0 else None

                if tag.find('div', {'class': 'gs_fl'}):
                    self._parse_links(tag.find('div', {'class': 'gs_fl'}))

        if self.article['title']:
            self.handle_article(self.article)


class ScholarQuery(object):
    """
    This is the base class for any kind of search query we send
    off. It includes the search query parameters the user is
    interested in. These are directly modelled after the search fields
    you see on the Scholar website in the advanced search options.
    """
    def __init__(self):
        self.words = None # The default search behavior
        self.words_some = None # At least one of those words
        self.words_none = None # None of these words
        self.phrase = None
        self.scope_title = False # If True, search in title only
        self.author = None 
        self.pub = None
        self.timeframe = [None, None]
        self.cluster = None
        self.num_results = ScholarConf.MAX_PAGE_RESULTS

    def set_words(self, words):
        """Sets words that *all* must be found in the result."""
        self.words = words

    def set_words_some(self, words):
        """Sets words of which *at least one* must be found in result."""
        self.words_some = words

    def set_words_none(self, words):
        """Sets words of which *none* must be found in the result."""
        self.words_none = words

    def set_phrase(self, phrase):
        """Sets phrase that must be found in the result exactly."""
        self.phrase = phrase

    def set_scope(self, title_only):
        """
        Sets Boolean indicating whether to search entire article or title
        only.
        """
        self.scope_title = title_only

    def set_author(self, author):
        """Sets names that must be on the result's author list."""
        self.author = author

    def set_pub(self, pub):
        """Sets the publication in which the result must be found."""
        self.pub = pub

    def set_timeframe(self, start=None, end=None):
        """
        Sets timeframe (in years as integer) in which result must have
        appeared. It's fine to specify just start or end, or both.
        """
        if start:
            start = ScholarUtils.ensure_int(start)
        if end:
            end = ScholarUtils.ensure_int(end)
        self.timeframe = [start, end]

    def set_cluster(self, cluster):
        """
        Sets search to a Google Scholar results cluster ID. This means
        we don't really conduct a search, we just pull up the
        information about a cluster we already know about.
        """
        msg = 'cluster ID must be numeric'
        self.cluster = ScholarUtils.ensure_int(cluster, msg)

    def set_num_page_results(self, num_page_results):
        msg = 'maximum number of results on page must be numeric'
        self.num_results = ScholarUtils.ensure_int(num_page_results, msg)


class ScholarSettings(object):

    """
    This class lets you adjust the Scholar settings for your
    session. It's intended to mirror the features tunable in the
    Scholar Settings pane, but right now it's a bit basic.
    """
    CITFORM_NONE = 0
    CITFORM_REFWORKS = 1
    CITFORM_REFMAN = 2
    CITFORM_ENDNOTE = 3
    CITFORM_BIBTEX = 4

    def __init__(self):
        self.citform = 0 # Citation format, default none
        self.per_page_results = ScholarConf.MAX_PAGE_RESULTS
        self._is_configured = False

    def set_citation_format(self, citform):
        citform = ScholarUtils.ensure_int(citform)
        if citform < 0 or citform > self.CITFORM_BIBTEX:
            raise FormatError('citation format invalid, is "%s"' \
                              % citform)
        self.citform = citform
        self._is_configured = True

    def set_per_page_results(self, per_page_results):
        msg = 'page results must be integer'
        self.per_page_results = ScholarUtils.ensure_int(per_page_results, msg)
        self.per_page_results = min(self.per_page_results,
                                    ScholarConf.MAX_PAGE_RESULTS)
        self._is_configured = True

    def is_configured(self):
        return self._is_configured


class ScholarQuerier(object):

    """
    ScholarQuerier instances can conduct a search on Google Scholar
    with subsequent parsing of the resulting HTML content.  The
    articles found are collected in the articles member, a list of
    ScholarArticle instances.
    """
    SCHOLAR_QUERY_URL = ScholarConf.SCHOLAR_SITE + '/scholar?' \
        + 'as_q=%(words)s' \
        + '&as_epq=%(phrase)s' \
        + '&as_oq=%(words_some)s' \
        + '&as_eq=%(words_none)s' \
        + '&as_occt=%(scope)s' \
        + '&as_sauthors=%(authors)s' \
        + '&as_publication=%(pub)s' \
        + '&as_ylo=%(ylo)s' \
        + '&as_yhi=%(yhi)s' \
        + '&btnG=&hl=en&as_sdt=0,5&num=%(num)s'

    # Default URLs for visiting and submitting Settings pane, as of 3/14
    GET_SETTINGS_URL = ScholarConf.SCHOLAR_SITE + '/scholar_settings?' \
        + 'sciifh=1&hl=en&as_sdt=0,5'

    SET_SETTINGS_URL = ScholarConf.SCHOLAR_SITE + '/scholar_setprefs?' \
        + 'q=' \
        + '&scisig=%(scisig)s' \
        + '&inststart=0' \
        + '&as_sdt=1,5' \
        + '&as_sdtp=' \
        + '&num=%(num)s' \
        + '&scis=%(scis)s' \
        + '%(scisf)s' \
        + '&hl=en&lang=all&instq=&inst=569367360547434339&save='

    # Older URLs:
    # ScholarConf.SCHOLAR_SITE + '/scholar?q=%s&hl=en&btnG=Search&as_sdt=2001&as_sdtp=on

    class Parser(ScholarArticleParser120726):
        def __init__(self, querier):
            ScholarArticleParser120726.__init__(self)
            self.querier = querier

        def handle_article(self, art):
            self.querier.add_article(art)

    def __init__(self):
        self.articles = []
        self.query = None
        self.cjar = MozillaCookieJar()

        # If we have a cookie file, load it:
        if ScholarConf.COOKIE_JAR_FILE and \
           os.path.exists(ScholarConf.COOKIE_JAR_FILE):
            try:
                self.cjar.load(ScholarConf.COOKIE_JAR_FILE,
                               ignore_discard=True)
                ScholarUtils.log('debug', 'loaded cookies file')
            except Exception as msg:
                ScholarUtils.log('warn', 'could not load cookies file: %s' % msg)
                self.cjar = MozillaCookieJar() # Just to be safe

        self.opener = build_opener(HTTPCookieProcessor(self.cjar))
        self.settings = None # Last settings object, if any

    def apply_settings(self, settings):
        """
        Applies settings as provided by a ScholarSettings instance.
        """
        if settings is None or not settings.is_configured():
            return True

        self.settings = settings

        # This is a bit of work. We need to actually retrieve the
        # contents of the Settings pane HTML in order to extract
        # hidden fields before we can compose the query for updating
        # the settings.
        try:
            req = Request(url=self.GET_SETTINGS_URL,
                          headers={'User-Agent': ScholarConf.USER_AGENT})
            hdl = self.opener.open(req)
            html = hdl.read()
        except Exception as err:
            ScholarUtils.log('debug', 'requesting settings failed: %s' % err)
            return False

        # Now parse the required stuff out of the form. We require the
        # "scisig" token to make the upload of our settings acceptable
        # to Google.
        soup = BeautifulSoup(html)

        tag = soup.find(name='form', attrs={'id': 'gs_settings_form'})
        if tag is None:
            ScholarUtils.log('debug', 'parsing settings failed: no form')
            return False

        tag = tag.find('input', attrs={'type':'hidden', 'name':'scisig'})
        if tag is None:
            ScholarUtils.log('debug', 'parsing settings failed: scisig')
            return False

        urlargs = {'scisig': tag['value'],
                   'num': settings.per_page_results,
                   'scis': 'no',
                   'scisf': '' }

        if settings.citform != 0:
            urlargs['scis'] = 'yes'
            urlargs['scisf'] = '&scisf=%d' % settings.citform

        try:
            req = Request(url=self.SET_SETTINGS_URL % urlargs,
                          headers={'User-Agent': ScholarConf.USER_AGENT})
            hdl = self.opener.open(req)
        except Exception as err:
            ScholarUtils.log('debug', 'applying settings failed: %s' % err)
            return False

        ScholarUtils.log('debug', 'settings applied')
        return True

    def send_query(self, query, scholar_url=None):
        """
        This method initiates a search query (a ScholarQuery instance)
        with subsequent parsing of the response.
        """
        self.clear_articles()
        self.query = query

        url = scholar_url if scholar_url else self.SCHOLAR_QUERY_URL

        urlargs = {'words': query.words or '',
                   'words_some': query.words_some or '',
                   'words_none': query.words_none or '',
                   'phrase': query.phrase or '',
                   'scope': 'title' if query.scope_title else 'any',
                   'authors': query.author or '',
                   'pub': query.pub or '',
                   'ylo': query.timeframe[0] or '',
                   'yhi': query.timeframe[1] or '',
                   'num': query.num_results or ScholarConf.MAX_PAGE_RESULTS } 

        # Make sure we urlencode all this stuff correctly:
        for key, val in urlargs.items():
            urlargs[key] = quote(str(val))

        url = url % urlargs

        ScholarUtils.log('debug', 'query url: %s' % url)
        req = Request(url=url, headers={'User-Agent': ScholarConf.USER_AGENT})
        hdl = self.opener.open(req)
        html = hdl.read()

        self.parse(html)

    def get_citation_data(self, article):
        """
        Given an article, retrieves citation link. Note, this requires that
        you adjusted the settings to tell Google Scholar to actually
        provide this information, *prior* to retrieving the article.
        """
        if article['citlink'] is None:
            return False
        if article.citation_data is not None:
            return True
        try:
            ScholarUtils.log('debug', 'retrieving citation export from %s' \
                             % article['citlink'])
            req = Request(url=article['citlink'],
                          headers={'User-Agent': ScholarConf.USER_AGENT})
            hdl = self.opener.open(req)
            data = hdl.read()
            article.set_citation_data(data)
        except Exception as err:
            ScholarUtils.log('debug', 'requesting citation failed: %s' % err)
            return False

        return True

    def parse(self, html):
        """
        This method allows parsing of provided HTML content.
        """
        parser = self.Parser(self)
        parser.parse(html)

    def add_article(self, art):
        self.get_citation_data(art)
        self.articles.append(art)

    def clear_articles(self):
        """Clears any existing articles stored from previous queries."""
        self.articles = []

    def save_cookies(self):
        """
        This stores the latest cookies we're using to disk, for reuse in a
        later session.
        """
        if ScholarConf.COOKIE_JAR_FILE is None:
            return False
        try:
            self.cjar.save(ScholarConf.COOKIE_JAR_FILE,
                           ignore_discard=True)
            ScholarUtils.log('debug', 'saved cookies file')
            return True
        except Exception as msg:
            ScholarUtils.log('warn', 'could not save cookies file: %s' % msg)
            return False
            

def txt(querier):
    articles = querier.articles
    for art in articles:
        print(art.as_txt() + '\n')

def csv(querier, header=False, sep='|'):
    articles = querier.articles
    for art in articles:
        result = art.as_csv(header=header, sep=sep)
        print(encode(result))
        header = False

def citation_export(querier):
    articles = querier.articles
    for art in articles:
        print(art.as_citation() + '\n')


def main():
    usage = """scholar.py [options] <query string>
A command-line interface to Google Scholar.

Examples:

# Retrieve one article written by Einstein on quantum theory:
scholar.py -c 1 --author "albert einstein" --phrase "quantum theory"

# Retrieve five articles written by Einstein after 1970 where the title
# does not contain the words "quantum" and "theory":
scholar.py -c 5 -a "albert einstein" -t --none "quantum theory" --after 1970

# Retrieve a BibTeX entry for that quantum theory paper:
scholar.py -c 1 --author "albert einstein" --phrase "quantum theory" --citation bt"""

    fmt = optparse.IndentedHelpFormatter(max_help_position=50, width=100)
    parser = optparse.OptionParser(usage=usage, formatter=fmt)
    group = optparse.OptionGroup(parser, 'Query arguments',
                                 'These options define search query arguments and parameters.')
    group.add_option('-a', '--author', metavar='AUTHORS', default=None,
                     help='Author name(s)')
    group.add_option('-A', '--all', metavar='WORDS', default=None, dest='allw',
                     help='Results must contain all of these words')
    group.add_option('-s', '--some', metavar='WORDS', default=None,
                     help='Results must contain at least one of these words')
    group.add_option('-n', '--none', metavar='WORDS', default=None,
                     help='Results must contain none of these words')
    group.add_option('-p', '--phrase', metavar='PHRASE', default=None,
                     help='Results must contain exact phrase')
    group.add_option('-t', '--title-only', action='store_true', default=False,
                     help='Search title only')
    group.add_option('-P', '--pub', metavar='PUBLICATIONS', default=None,
                     help='Results must have appeared in this publication')
    group.add_option('--after', metavar='YEAR', default=None,
                     help='Results must have appeared in or after given year')
    group.add_option('--before', metavar='YEAR', default=None,
                     help='Results must have appeared in or before given year')                    
    group.add_option('-c', '--count', type='int', default=None,
                     help='Maximum number of results')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Output format',
                                 'These options control the appearance of the results.')
    group.add_option('--txt', action='store_true',
                     help='Print article data in text format (default)')
    group.add_option('--csv', action='store_true',
                     help='Print article data in CSV form (separator is "|")')
    group.add_option('--csv-header', action='store_true',
                     help='Like --csv, but print header with column names')
    group.add_option('--citation', metavar='FORMAT', default=None,
                     help='Print article details in standard citation format. Argument Must be one of "bt" (BibTeX), "en" (EndNote), "rm" (RefMan), or "rw" (RefWorks).')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Miscellaneous')
    group.add_option('--cookie-file', metavar='FILE', default=None,
                     help='File to use for cookie storage. If given, will read any existing cookies if found at startup, and save resulting cookies in the end.')
    group.add_option('-d', '--debug', action='store_true', default=False,
                     help='Enable verbose logging to stderr')
    group.add_option('-v', '--version', action='store_true', default=False,
                     help='Show version information')
    parser.add_option_group(group)

    options, args = parser.parse_args()

    # Show help if we have neither keyword search nor author name
    if len(sys.argv) == 1:
        parser.print_help()
        return 1

    if options.debug:
        ScholarConf.LOG_LEVEL = ScholarUtils.LOG_LEVELS['debug']

    if options.version:
        print 'This is scholar.py %s.' % ScholarConf.VERSION
        return 0

    if options.cookie_file:
        ScholarConf.COOKIE_JAR_FILE = options.cookie_file

    querier = ScholarQuerier()
    settings = ScholarSettings()

    if options.citation == 'bt':
        settings.set_citation_format(ScholarSettings.CITFORM_BIBTEX)
    elif options.citation == 'en':
        settings.set_citation_format(ScholarSettings.CITFORM_ENDNOTE)
    elif options.citation == 'rm':
        settings.set_citation_format(ScholarSettings.CITFORM_REFMAN)
    elif options.citation == 'rw':
        settings.set_citation_format(ScholarSettings.CITFORM_REFWORKS)
    elif options.citation is not None:
        print 'Invalid citation link format, must be one of "bt", "en", "rm", or "rw".'
        return 1

    querier.apply_settings(settings)

    query = ScholarQuery()

    if options.author:
        query.set_author(options.author)
    if options.allw:
        query.set_words(options.allw)
    if options.some:
        query.set_words_some(options.some)
    if options.none:
        query.set_words_none(options.none)
    if options.phrase:
        query.set_phrase(options.phrase)
    if options.title_only:
        query.set_scope(True)
    if options.pub:
        query.set_pub(options.pub)
    if options.after or options.before:
        query.set_timeframe(options.after, options.before)
    if options.count is not None:
        options.count = min(options.count, ScholarConf.MAX_PAGE_RESULTS)
        query.set_num_page_results(options.count)

    querier.send_query(query)

    if options.csv:
        csv(querier)
    elif options.csv_header:
        csv(querier, header=True)
    elif options.citation is not None:
        citation_export(querier)
    else:
        txt(querier)

    if options.cookie_file:
        querier.save_cookies()

    return 0

if __name__ == "__main__":
    sys.exit(main())
