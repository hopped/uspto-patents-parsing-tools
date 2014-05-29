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

import codecs
from sgmllib import SGMLParser
from cStringIO import StringIO
from getopt import getopt
from getopt import GetoptError
from sys import argv
from sys import exit
from time import time
import os
import zipfile

__author__ = 'Dennis Hoppe'
__email__ = 'hoppe.dennis@ymail.com'
__status__ = 'Development'

class FileHandler():
  def __init__(self, zfile):
    self.zfile = zfile

  def readline(self):
    return self.zfile.readline()

  def listXmls(self):
    output = StringIO()
    line = self.readline()
    line = line[0:len(line)-3]
    line = line + ' \"\" [\n'
    output.write(line)
    line = self.readline()
    while line is not '':
      if '<!DOCTYPE PATDOC PUBLIC "-//USPTO//DTD' in line:
        yield output
        output = StringIO()
        if '[]' in line:
          pass#line = line.replace('[]>', ' \"st32-us-grant-024nf.dtd\" []>\n')
        else:
          pass#line = line.replace('\"\"', '\"st32-us-grant-024nf.dtd\" [\n')
        output.write(line)
        try:
          line = self.readline()
        except StopIteration:
          break
        output.write(line)
        try:
          line = self.readline()
        except StopIteration:
          break
        while not '<PATDOC' in line:
          output.write(line)
          try:
            line = self.readline()
          except StopIteration:
            break
        #end while
      elif 'CITED-BY-EXAMINER' in line:
        line = line.replace('<CITED-BY-EXAMINER>', '')
        output.write(line)
      elif 'B597US' in line:
        line = line.replace('<B597US>', '')
        output.write(line)
      else:
        output.write(line)
      try:
        line = self.readline()
      except StopIteration:
        break
    output.seek(0)
    yield output


class SimpleXMLHandler(SGMLParser):
  '''
  B110 Document Number
  B140 Document Date (publication or issue)
  B510 International Patent Classification (IPC) Data (B511, B512, not B516)
  B520 Domestic or National Classification Data (B521)
  B540 Title of Invention
  B570 Abstract or Design Claim and Figure Description
  B721 Inventor name, address, and residence.
  B730 Assignee (grantee, assignee, holder, owner) (B731)
  '''
  def __init__(self):
    SGMLParser.__init__(self, False)
    # gather data
    self.information = []
    # states
    self.document_id = 0
    self.date = 0
    self.ipc_data = 0
    self.usc_data = 0
    self.title = 0
    self.inventor = 0
    self.assignee = 0
    self.abstract = 0
    self.readable = 0
    # buffers
    self.docid_buffer = ''
    self.date_buffer = ''
    self.ipc_buffer = ''
    self.usc_buffer = ''
    self.title_buffer = ''
    self.inventor_buffer = ''
    self.assignee_buffer = ''
    self.abstract_buffer = ''

  def unknown_starttag(self, tag, attributes):
    if tag == 'b110':
      self.document_id = 1
    elif tag == 'b140':
      self.date = 1
    elif tag == 'b511' or tag == 'b512':
      self.ipc_data = 1
    elif tag == 'b521':
      self.usc_data = 1
    elif tag == 'b540':
      self.title = 1
    elif tag == 'b721':
      self.inventor = 1
    elif tag == 'b731':
      self.assignee = 1
    elif tag == 'nam':
      self.readable = 1
    elif tag == 'sdoab':
      self.abstract = 1

  def handle_data(self, data):
    if self.document_id == 1:
      self.docid_buffer = self.docid_buffer + data
    elif self.date == 1:
      self.date_buffer = self.date_buffer + data
    elif self.ipc_data == 1:
      self.ipc_buffer = self.ipc_buffer + data
    elif self.usc_data == 1:
      self.usc_buffer = self.usc_buffer + data
    elif self.title == 1:
      self.title_buffer = self.title_buffer + data
    elif self.inventor == 1 and self.readable == 1:
      self.inventor_buffer = self.inventor_buffer + data + ' '
    elif self.assignee == 1 and self.readable == 1:
      self.assignee_buffer = self.assignee_buffer + data + ' '
    elif self.abstract == 1:
      self.abstract_buffer = self.abstract_buffer + data

  def unknown_endtag(self, tag):
    if tag == 'b110':
      self.information.append('ID/' + self.docid_buffer)
      self.docid_buffer = ''
      self.document_id = 0
    elif tag == 'b140':
      self.information.append('APD/' + self.date_buffer)
      self.date_buffer = ''
      self.date = 0
    elif tag == 'b511' or tag == 'b512':
      self.information.append('ICL/' + self.ipc_buffer)
      self.ipc_buffer = ''
      self.ipc_data = 0
    elif tag == 'b521':
      self.information.append('CCL/' + self.usc_buffer)
      self.usc_buffer = ''
      self.usc_data = 0
    elif tag == 'b540':
      self.information.append('TTL/\"' + self.title_buffer + '\"')
      self.title_buffer = ''
      self.title = 0
    elif tag == 'b721':
      self.information.append('INV/\"' + self.inventor_buffer.strip() + '\"')
      self.information.append('ICN/US') # only party-us allowed
      self.inventor_buffer = ''
      self.inventor = 0
    elif tag == 'b731':
      self.information.append('AS/\"' + self.assignee_buffer.strip() + '\"')
      self.information.append('ACN/US') # only party-us allowed
      self.assignee_buffer = ''
      self.assignee = 0
    elif tag == 'nam':
      self.readable = 0
    elif tag == 'sdoab':
      self.information.append('ABST/\"' + self.abstract_buffer.strip() + '\"')
      self.abstract_buffer = ''
      self.abstract = 0

  def output(self):
    return self.information


def main(argv):
  """  SGML Parser for granted patents by the USPTO in 2001

  Usage: python uspto-sgml-parser.py [options] [source]

  Options:
    -h, --help            show this help
    -f .., --file=...
    -p .., --path=...     path to UPSTO patent applications
    -o .., --output=...   file to write results
    -l .., --limit-to=... limit parsing to a specific year
    -d, --load-dtd        if set, then the DTD is loaded (e.g., 2001)

  Examples:
    uspto-sgml-parser.py -p /media/backup_/patents/upsto-pair/appl_full_texts

  Issues:
    Parsing SGML is very slow due to '<!DOCTYPE PATDOC PUBLIC' checking. Implement
    a character-based check instead of line-based checking.

    Granted patents from 2001 do not contain abstracts.
  """

  dtd = False
  limit = None
  folder_in = None
  file_in = None
  out_file = 'names-in-patents.txt'
  try:
    opts, args = getopt(argv, 'dl:o:p:f:h', ['load-dtd', 'limit-to', 'output', 'file', 'path', 'help'])
  except GetoptError:
    usage()
    exit(2)
  for opt, arg in opts:
    if opt in ('-h', '--help'):
      usage()
      exit()
    if opt in ('-p', '--path'):
      if not os.path.isdir(arg):
        usage()
        exit(2)
      folder_in = arg
    if opt in ('-f', '--file'):
      if not os.path.isfile(arg):
        usage()
        exit(2)
      file_in = arg
    if opt in ('-o', '--output'):
      if os.path.isdir(arg):
        usage()
        exit(2)
      out_file = arg
    if opt in ('-l', '--limit-to'):
      limit = arg
    if opt in ('-d', '--load-dtd'):
      dtd = True

  write_buffer = codecs.open(out_file, 'w', 'utf-8')
  patents_count = 0

  if file_in is not None:
    start = time()
    f = open(file_in, 'rU')
    parser = SimpleXMLHandler()
    parser.feed(f.read())
    result = parser.output()
    write_buffer.write('FILE/' + os.path.basename(file_in) + '\t')
    for applicant in result:
      write_buffer.write(applicant)
      write_buffer.write('\t')
    write_buffer.write('\n')
    write_buffer.flush()
    elapsed = (time() - start)
    print str(elapsed) + ' seconds elapsed in total.'
  elif folder_in is not None:
    file_count = 0
    for folder in os.listdir(folder_in):
      folder = folder_in + '/' + folder
      if os.path.isdir(folder):
        if limit is not None:
          if not folder.endswith(limit):
            continue
        for zip_file in os.listdir(folder):
          zip_file = folder + '/' + zip_file
          if not zip_file.endswith('zip'):
            continue
          if zip_file.endswith('pa030501.zip'):
            continue # that file is corrupt
          try:
            zfile = zipfile.ZipFile(zip_file, 'r')
          except zipfile.BadZipfile:
            continue
          print 'process ' + str(zip_file)
          patents_within_document = 0
          start = time()
          ct = 0
          for name in zfile.namelist():
            if not name.endswith('.sgml'):
              continue
            f = FileHandler(zfile.open(name, 'rU'))
            for elem in f.listXmls():
              ct = ct+1
              # debug start
              #z = codecs.open('debug' + str(ct) + '.txt', 'w', 'utf-8')
              #z.write(elem.getvalue())
              #z.close()
              # debug en
              parser = SimpleXMLHandler()
              parser.feed(elem.getvalue())
              result = parser.output()
              write_buffer.write('FILE/' + os.path.basename(name) + '\t')
              for applicant in result:
                write_buffer.write(applicant)
                write_buffer.write('\t')
              write_buffer.write('\n')
              write_buffer.flush()
              patents_count = patents_count + 1
              patents_within_document = patents_within_document + 1
            zfile.close()
          print str(patents_within_document) + ' patents parsed.'
          elapsed = (time() - start)
          print str(elapsed) + ' seconds elapsed in total.'
    print str(patents_count) + ' patents examined.'
  #fi

def usage():
  print main.__doc__

if __name__ == "__main__":
  main(argv[1:])

# EOF
