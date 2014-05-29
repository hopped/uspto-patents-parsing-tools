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
    try:
      line = self.readline()
      line = self.readline()
      output.write(line)
      line = self.readline()
    except StopIteration:
      print 'error'
      return
    while line is not '':
      if 'PATN' in line:
        output.seek(0)
        yield output
        output = StringIO()
        output.write(line)
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
    self.states = {}
    self.states['INVT'] = 0
    self.states['ASSG'] = 0
    self.states['CLAS'] = 0
    self.states['ABST'] = 0
    self.states['PATN'] = 0

  def feed(self, text):
    lines = text.split('\n')
    for line in lines:
      if ' ' in line: # data field
        data = line[3:]
        if data[0] is not ' ':
          data = line[1:]
        data = data.lstrip()
      else: # change state
        for k in self.states.keys():
          self.states[k] = 0
        if line in self.states:
          self.states[line] = 1

      if line.startswith('APN'):
        if self.states['PATN'] == 1:
          self.information.append('ID/' + data)
      if line.startswith('APD'):
        if self.states['PATN'] == 1:
          self.information.append('APD/' + data)
      elif line.startswith('TTL'):
        if self.states['PATN'] == 1:
          self.information.append('TTL/\"' + data + '\"')
      elif line.startswith('NAM'):
        if self.states['INVT'] == 1:
          tokens = data.split(';')
          name = tokens[1].strip() + ' ' + tokens[0].strip()
          self.information.append('INV/\"' + name + '\"')
        elif self.states['ASSG'] == 1:
          self.information.append('AS/\"' + data + '\"')
      elif line.startswith('CNT'):
        if self.states['INVT'] == 1:
          self.information.append('ICN/' + data)
        elif self.states['ASSG'] == 1:
          self.information.append('ACN/' + data)
      elif line.startswith('OCL'):
        if self.states['CLAS'] == 1:
          self.information.append('CCL/' + data)
      elif line.startswith('ICL'):
        if self.states['CLAS'] == 1:
          self.information.append('ICL/' + data)
      elif line.startswith('PAL'):
        if self.states['ABST'] == 1:
          self.information.append('ABST/\"' + data + '\"')

  def output(self):
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
            if name.endswith('lst.txt') or name.endswith('rpt.txt'):
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
