#!/bin/bash/env python
"""
The MIT License

Copyright (c) 2014 Dennis Hoppe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from BeautifulSoup import BeautifulSoup
from collections import defaultdict
import errno
from getopt import getopt
from getopt import GetoptError
import logging
import os
import re
from sys import argv
from sys import exit
import urlgrabber
import urlgrabber.progress
import urllib2

__author__ = 'Dennis Hoppe'
__email__ = 'hoppe.dennis@ymail.com'
__status__ = 'Development'

def main(argv):
  """Download utility to simplify the download of USPTO patent data

  USPTO patent applications are currently hosted by Google. In most cases, you
  will be interested in all patents from a specific year or which lie in a
  relevant period of time. Since downloading each compressed file separately
  is cumbersome, this download utility might help you.

  This tools offers three basic operations:
  (1) -d  Downloads the relevant files one at a time; might be slow.
  (2) -f  Lists all available hyperlinks pointing to zip files, and store them
      in year-based text files. This is suitable for all that want to use their
      own donwload utility (e.g. parallelise the downloads).
  (3) -p  Prints all links found to zip files to the standard out


  Usage: python uspto-patent-downloader.py [options]

  Options:
    -d .., --download     downloads each zip file found using 'url'
    -f .., --files        writes all relevant links found into files; one file for each year
    -h, --help            shows this help
    -l .., --loglevel ... determines the log level (INFO, DEBUG, ..)
    -o .., --out ...      specifies the output directory
                          (default: './uspto-files')
    -p, --print           prints all relevant links found to the standard out
                          (this option is selected per default if '-f' is misssing)
    -u .., --url ...      url to the USPTO patent applications bibliography hosted by Google
                          (default: http://www.google.com/googlebooks/uspto-patents-applications-biblio.html)
    -y .., --years ...    comma separated list of years (e.g. '2002,2004') to consider for download
                          (default: all years are considered from 2001 to now)

  Examples:
    uspto-patent-downloader.py -list > links-to-download.txt
    uspto-patent-downloader.py -u http://www.google.com/googlebooks/uspto-patents-applications-biblio.html -f
    uspto-patent-downloader.py -years 2001,2002
    uspto-patent-downloader.py -f -y 2003 -out .
  """

  defaults = {
    'uspto_url': 'http://www.google.com/googlebooks/uspto-patents-applications-biblio.html',
    'html_page': None,
    'requested_years': [],
    'write_to_stdout': False,
    'print_to_file': False,
    'download': False,
    'output_directory': '.'
  }

  validate_input(argv, defaults);

  if not defaults['html_page']:
    defaults['html_page'] = load_url(uspto_url)
  soup = BeautifulSoup(html_page)

  links_per_year = defaultdict(list)
  links = soup.findAll('a', attrs={ 'href': re.compile('zip$') })
  logging.info(' found ' + str(len(links)) + ' links')
  for link in links:
    logging.debug('  . ' + link['href'])
    matched_year = re.search( '/([0-9]{4})/', link['href'])
    if matched_year:
      links_per_year[matched_year.group(1)].append(link['href'])
  filtered_dict = links_per_year
  if requested_years:
    filtered_dict = { year : links_per_year[year] for year in requested_years }
  if write_to_stdout:
    for links in sorted(filtered_dict.itervalues()):
      for link in links:
        print link
  if print_to_file:
    makedirs(output_directory)
    for k,v in filtered_dict.iteritems():
      basename = k + '.txt'
      filename = output_directory + '/' + basename
      if os.path.isfile(filename):
        os.remove(filename)
      with open(filename, 'a') as text_file:
        for link in sorted(v):
          text_file.write(link + '\n')
        logging.debug(' file ' + basename + ' written to disk')
    logging.info(' all files written to disk')
  if download:
    for year, links in filtered_dict.iteritems():
      makedirs(os.path.join(output_directory, year))
      for link in links:
        try:
          filename = os.path.join(output_directory, year, link.split('/')[-1])
          prog = urlgrabber.progress.text_progress_meter()
          urlgrabber.urlgrab(str(link), filename, progress_obj=prog)
        except Exception, e:
          logging.warn(' error while downloading %s: %s' % (link, e))

def validate_input(argv, defaults):
  try:
    opts, args = getopt(argv, 'dpy:o:u:hl:f',
      ['download', 'print', 'years', 'output', 'url', 'help', 'loglevel', 'files'])
  except GetoptError:
    usage()
    exit(2)

  if not opts:
    usage()
    exit()

  options = {
    '-h': option_help,
    '--help': option_help,
    '-u': option_url,
    '--url': option_url,
    '-d': option_download,
    '--download': option_download,
    '-f': option_files,
    '--files': option_files,
    '-y': option_years,
    '--years': option_years,

  }
  for opt, arg in opts:
    options.get(opt, option_default)(defaults, arg)

def option_default(defaults, arg):
  raise ValueError('value unsupported')

def option_download(defaults, arg):
  defaults['download'] = True

def option_files(defaults, arg):
  defaults['print_to_file'] = True

def option_help(defaults, arg):
  usage()
  exit()

def option_logging(defaults, arg):
  numeric_level = getattr(logging, arg.upper(), None)
  if not isinstance(numeric_level, int):
    raise ValueError('invalid log level: %s' % arg)
  logging.basicConfig(level=numeric_level)

def option_output(defaults, arg):
  makedirs(arg)
  defaults['output'] = arg

def option_print(defaults, arg):
  defaults['write_to_stdout'] = True

def option_url(defaults, arg):
  defaults['html_page'] = load_url(arg)

def option_years(defaults, arg):
  defaults['requested_years'] = arg.split(',')

def makedirs(path):
  try:
    os.makedirs(path)
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise

def load_url(request):
  logging.info(' requesting ' + request + ' ...')
  try:
    return urllib2.urlopen(request)
  except urllib2.HTTPError, e:
    logging.warning(' url: ' + request + '; HTTPError = ' + str(e.code))
  except urllib2.URLError, e:
    logging.warning(' url: ' + request + '; URLError = ' + str(e.reason))
  except httplib.HTTPException, e:
    logging.warning(' url: ' + request + '; HTTPException')
  exit()

def usage():
  print main.__doc__

if __name__ == "__main__":
  main(argv[1:])

# EOF
