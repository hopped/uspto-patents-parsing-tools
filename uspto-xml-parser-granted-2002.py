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
from cStringIO import StringIO
from getopt import getopt
from getopt import GetoptError
from lxml import etree
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
    output.write(line)
    line = self.readline()
    while line is not '':
      if '<?xml version="1.0" encoding="UTF-8"?>' in line:
        line = line.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
        output.write(line)
        output.seek(0)
        yield output
        output = StringIO()
        output.write('<?xml version="1.0" encoding="UTF-8"?>')
      elif '<?xml version="1.0"?>' in line:
        line = line.replace('<?xml version="1.0"?>', '')
        output.write(line)
        output.seek(0)
        yield output
        output = StringIO()
        output.write('<?xml version="1.0"?>')
      else:
        output.write(line)
      try:
        line = self.readline()
      except StopIteration:
        break
    output.seek(0)
    yield output


class SimpleXMLHandler(object):
  '''
  B110  Document Number
  B140  Document Date (publication or issue)
  B510  International Patent Classification (IPC) Data (B511, B512, not B516)
  B520  Domestic or National Classification Data (B521)
  B540  Title of Invention
  B570  Abstract or Design Claim and Figure Description
  B721  Inventor name, address, and residence.
  B730  Assignee (grantee, assignee, holder, owner) (B731)
  SDOAB Abstract
  '''
  def __init__(self):
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

  def start(self, tag, attributes):
    if tag == 'B110':
      self.document_id = 1
    elif tag == 'B140':
      self.date = 1
    elif tag == 'B511' or tag == 'B512':
      self.ipc_data = 1
    elif tag == 'B521':
      self.usc_data = 1
    elif tag == 'B540':
      self.title = 1
    elif tag == 'B721':
      self.inventor = 1
    elif tag == 'B731':
      self.assignee = 1
    elif tag == 'NAM':
      self.readable = 1
    elif tag == 'SDOAB':
      self.abstract = 1

  def data(self, data):
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

  def end(self, tag):
    if tag == 'B110':
      self.information.append('ID/' + self.docid_buffer)
      self.docid_buffer = ''
      self.document_id = 0
    elif tag == 'B140':
      self.information.append('APD/' + self.date_buffer)
      self.date_buffer = ''
      self.date = 0
    elif tag == 'B511' or tag == 'B512':
      self.information.append('ICL/' + self.ipc_buffer)
      self.ipc_buffer = ''
      self.ipc_data = 0
    elif tag == 'B521':
      self.information.append('CCL/' + self.usc_buffer)
      self.usc_buffer = ''
      self.usc_data = 0
    elif tag == 'B540':
      self.information.append('TTL/\"' + self.title_buffer + '\"')
      self.title_buffer = ''
      self.title = 0
    elif tag == 'B721':
      self.information.append('INV/\"' + self.inventor_buffer.strip() + '\"')
      self.information.append('ICN/US') # only party-us allowed
      self.inventor_buffer = ''
      self.inventor = 0
    elif tag == 'B731':
      self.information.append('AS/\"' + self.assignee_buffer.strip() + '\"')
      self.information.append('ACN/US') # only party-us allowed
      self.assignee_buffer = ''
      self.assignee = 0
    elif tag == 'NAM':
      self.readable = 0
    elif tag == 'SDOAB':
      self.information.append('ABST/\"' + self.abstract_buffer.strip() + '\"')
      self.abstract_buffer = ''
      self.abstract = 0

  def close(self):
    return self.information


def main(argv):
  """  XML Parser for USPTO patent files

  Usage: python uspto-xml-parser.py [options] [source]

  Options:
    -h, --help            show this help
    -f .., --file=...
    -p .., --path=...     path to UPSTO patent applications
    -o .., --output=...   file to write results
    -l .., --limit-to=... limit parsing to a specific year
    -d, --load-dtd        if set, then the DTD is loaded (e.g., 2001)

  Examples:
    uspto-xml-parser.py -p /media/backup_/patents/upsto-pair/appl_full_texts

  Issues:
    The file '2003/pa030501.zip' is corrupt. While parsing, one encounters
    a long sequence of chars 0x0 ending not well-formed. The patent is currently
    discarded.

    Parsing XML is very slow due to '<?xml version' checking. Implement
    a character-based check instead of line-based checking.
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
    parser = etree.XMLParser(target=SimpleXMLHandler(), resolve_entities=False, load_dtd=dtd)
    result = etree.parse(f, parser)
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
            if not name.endswith('.xml'):
              continue
            f = FileHandler(zfile.open(name, 'rU'))
            for elem in f.listXmls():
              ct = ct+1
              # debug start
              #z = codecs.open('debug' + str(ct) + '.txt', 'w', 'utf-8')
              #z.write(elem.getvalue())
              #z.close()
              # debug en
              parser = etree.XMLParser(target=SimpleXMLHandler(), resolve_entities=False, load_dtd=dtd)
              result = etree.parse(elem, parser)
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
