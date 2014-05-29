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
  def __init__(self):
    ''' xml elements '''
    self.last_name = 0
    self.first_name = 0
    self.given_name = 0
    self.middle_name = 0
    self.family_name = 0
    self.organization_name = 0
    self.inventor = 0
    self.assignee = 0
    self.country_code = 0
    self.document_date = 0
    self.pct_application = 0
    self.ipc = 0
    self.primary_ipc = 0
    self.primary_uspc = 0
    self.title = 0
    self.abstract = 0
    self.document_id = 0
    self.set_id = False
    self.code_class = 0
    self.subclass = 0
    self.section = 0
    self.group = 0
    self.subgroup = 0
    self.references_cited = 0
    self.publication_reference = 0
    self.addressbook = 0
    self.classification_search = 0
    ''' buffer '''
    self.buffer = ''
    self.firstname_buffer = ''
    self.lastname_buffer = ''
    self.organization_buffer = ''
    self.given_name_buffer = ''
    self.middle_name_buffer = ''
    self.family_name_buffer = ''
    self.country_buffer = ''
    self.date_buffer = ''
    self.ipc_buffer = ''
    self.uspc_buffer = ''
    self.title_buffer = ''
    self.abstract_buffer = ''
    self.id_buffer = ''
    ''' storage '''
    self.write_buffer = []

  def start(self, tag, attributes):
    if tag == 'last-name':
      self.last_name = 1
    elif tag == 'first-name':
      self.first_name = 1
    elif tag == 'given-name':
      self.given_name = 1
    elif tag == 'middle-name':
      self.middle_name = 1
    elif tag == 'family-name':
      self.family_name = 1
    elif tag == 'organization-name' or tag == 'orgname':
      self.organization_name = 1
    elif tag == 'inventors' or tag == 'applicants':
      self.inventor = 1
    elif tag == 'assignees' or tag == 'assignee':
      self.assignee = 1
    elif tag == 'country-code' or tag == 'country':
      self.country_code = 1
    elif tag == 'classification-ipc-primary' or tag == 'classification-ipcr':
      self.primary_ipc = 1
    elif tag == 'ipc':
      self.ipc = 1
    elif tag == 'class':
      self.code_class = 1
    elif tag == 'subclass':
      self.subclass = 1
    elif tag == 'section':
      self.section = 1
    elif tag == 'main-group':
      self.group = 1
    elif tag == 'subgroup' or tag == 'main-classification':
      self.subgroup = 1
    elif tag == 'references-cited':
      self.references_cited = 1
    elif tag == 'classification-us-primary' or tag == 'classification-national':
      self.primary_uspc = 1
    elif tag == 'document-id':
      self.pct_application = 1
    elif tag == 'addressbook' or tag == 'name':
      self.addressbook = 1
    elif tag == 'document-date' or tag == 'date':
      self.document_date = 1
    elif tag == 'title-of-invention' or tag == 'invention-title':
      self.title = 1
    elif tag == 'subdoc-abstract' or tag == 'abstract':
      self.abstract = 1
    elif tag == 'doc-number':
      self.document_id = 1
    elif tag == 'us-field-of-classification-search':
      self.classification_search = 1

  def data(self, data):
    if self.last_name == 1:
      self.lastname_buffer += data
    elif self.first_name == 1:
      self.firstname_buffer += data
    elif self.given_name == 1:
      self.given_name_buffer += data
    elif self.middle_name == 1:
      self.middle_name_buffer += data
    elif self.family_name == 1:
      self.family_name_buffer += data
    elif self.organization_name == 1:
      self.organization_buffer += data
    elif self.country_code == 1:
      self.country_buffer += data
    elif self.document_date == 1:
      self.date_buffer += data
    elif self.ipc == 1:
      self.ipc_buffer += data
    elif self.code_class == 1:
      self.ipc_buffer += data
      self.uspc_buffer += data
    elif self.subclass == 1:
      self.ipc_buffer += data
    elif self.code_class == 1:
      self.ipc_buffer += data
    elif self.section == 1:
      self.ipc_buffer += data
    elif self.group == 1:
      self.ipc_buffer += data
    elif self.subgroup == 1:
      self.ipc_buffer += data
      self.uspc_buffer += data
    elif self.title == 1:
      self.title_buffer += data
    elif self.abstract == 1:
      self.abstract_buffer += data
    elif self.document_id == 1:
      self.id_buffer += data

  def end(self, tag):
    if tag == 'last-name':
      self.last_name = 0
    elif tag == 'first-name':
      if self.inventor == 1:
        self.firstname_buffer += ' '
        self.write_buffer.append("INV/\"" + self.firstname_buffer + self.lastname_buffer + "\"")
      self.firstname_buffer = ''
      self.lastname_buffer = ''
      self.first_name = 0
    elif tag == 'given-name':
      self.given_name = 0
    elif tag == 'middle-name':
      self.middle_name = 0
    elif tag == 'family-name':
      if self.inventor == 1:
        self.given_name_buffer += ' '
        if self.middle_name_buffer != '':
          self.given_name_buffer += self.middle_name_buffer
          self.given_name_buffer += ' '
        self.write_buffer.append("INV/\"" + self.given_name_buffer + self.family_name_buffer + "\"")
      self.given_name_buffer = ''
      self.middle_name_buffer = ''
      self.family_name_buffer = ''
      self.family_name = 0
    elif tag == 'organization-name' or tag == 'orgname':
      if self.assignee == 1:
        self.write_buffer.append("AS/\"" + self.organization_buffer.strip() + "\"")
      self.organization_buffer = ''
      self.organization_name = 0
    elif tag == 'inventors' or tag == 'applicants':
      self.inventor = 0
    elif tag == 'assignees' or tag == 'assignee':
      self.assignee = 0
    elif tag == 'addressbook' or tag == 'name':
      self.addressbook = 0
    elif tag == 'country-code' or tag == 'country':
      if self.inventor == 1:
        self.write_buffer.append("ICN/" + self.country_buffer);
      elif self.assignee == 1:
        self.write_buffer.append("ACN/" + self.country_buffer);
      self.country_buffer = ''
      self.country_code = 0
    elif tag == 'doc-number':
      if self.set_id == False:
        self.write_buffer.append("ID/" + self.id_buffer);
      self.id_buffer = ''
      self.document_id = 0
    elif tag == 'document-date' or tag == 'date':
      if self.set_id == False:
        self.write_buffer.append("APD/" + self.date_buffer);
        self.set_id = True
      self.date_buffer = ''
      self.document_date = 0
    elif tag == 'document-id':
      self.pct_application = 0
    elif tag == 'publication-reference':
      self.pct_application = 1
    elif tag == 'classification-ipc-primary' or tag == 'classification-ipcr':
      self.primary_ipc = 0
    elif tag == 'ipc':
      if self.primary_ipc == 1:
        self.write_buffer.append("ICL/" + self.ipc_buffer);
      self.ipc_buffer = ''
      self.ipc = 0
    elif tag == 'classification-us-primary' or tag == 'classification-national':
      self.primary_uspc = 0
    elif tag == 'class':
      self.code_class = 0
    elif tag == 'subclass':
      if self.primary_uspc == 1:
        self.write_buffer.append("CCL/" + self.uspc_buffer);
      if self.ipc != 1:
        self.uspc_buffer = ''
      self.subclass = 0
    elif tag == 'section':
      self.section = 0
    elif tag == 'main-group':
      self.group = 0
    elif tag == 'subgroup' or tag == 'main-classification':
      if self.references_cited == 0 and self.classification_search == 0:
        if self.primary_uspc == 1:
          self.write_buffer.append("CCL/" + self.uspc_buffer.strip());
        elif self.primary_ipc == 1:
          self.write_buffer.append("ICL/" + self.ipc_buffer.strip());
      self.uspc_buffer = ''
      self.ipc_buffer = ''
      self.subgroup = 0
    elif tag == 'title-of-invention' or tag == 'invention-title':
      self.write_buffer.append("TTL/\"" + self.title_buffer + "\"");
      self.title_buffer = ''
      self.title = 0
    elif tag == 'subdoc-abstract' or tag == 'abstract':
      if self.abstract_buffer != '':
        self.abstract_buffer = self.abstract_buffer.expandtabs(1)
        self.abstract_buffer = ' '.join(self.abstract_buffer.splitlines())
        self.abstract_buffer = self.abstract_buffer.strip()
        self.write_buffer.append("ABST/\"" + self.abstract_buffer + "\"");
      self.abstract_buffer = ''
      self.abstract = 0
    elif tag == 'references-cited':
      self.references_cited = 0
    elif tag == 'us-field-of-classification-search':
      self.classification_search = 0

  def close(self):
    return self.write_buffer


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
          for name in zfile.namelist():
            if not name.endswith('.xml'):
              continue
            f = FileHandler(zfile.open(name, 'rU'))
            for elem in f.listXmls():
              # debug start
              #z = codecs.open('debug.txt', 'w', 'utf-8')
              #z.write(elem.getvalue())
              #z.close()
              # debug end
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
