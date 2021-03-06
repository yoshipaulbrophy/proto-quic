#!/usr/bin/env python
# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Collect, archive, and analyze Chrome's binary size."""

import argparse
import atexit
import collections
import distutils.spawn
import logging
import os
import platform
import resource
import sys

import archive
import console
import html_report


def _LogPeakRamUsage():
  peak_ram_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  peak_ram_usage += resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
  logging.info('Peak RAM usage was %d MB.', peak_ram_usage / 1024)


def _AddCommonArguments(parser):
  parser.add_argument('--no-pypy', action='store_true',
                      help='Do not automatically switch to pypy when available')
  parser.add_argument('-v',
                      '--verbose',
                      default=0,
                      action='count',
                      help='Verbose level (multiple times for more)')


class _DiffAction(object):
  @staticmethod
  def AddArguments(parser):
    parser.add_argument('before', help='Before-patch .size file.')
    parser.add_argument('after', help='After-patch .size file.')
    parser.add_argument('--all', action='store_true', help='Verbose diff')

  @staticmethod
  def Run(args, parser):
    args.output_directory = None
    args.tool_prefix = None
    args.inputs = [args.before, args.after]
    args.query = ('Print(Diff(size_info1, size_info2), verbose=%s)' %
                  bool(args.all))
    console.Run(args, parser)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  sub_parsers = parser.add_subparsers()
  actions = collections.OrderedDict()
  actions['archive'] = (archive, 'Create a .size file')
  actions['html_report'] = (
      html_report, 'Create a stand-alone html report from a .size file.')
  actions['console'] = (
      console,
      'Starts an interactive Python console for analyzing .size files.')
  actions['diff'] = (
      _DiffAction(),
      'Shorthand for console --query "Print(Diff(size_info1, size_info2))"')

  for name, tup in actions.iteritems():
    sub_parser = sub_parsers.add_parser(name, help=tup[1])
    _AddCommonArguments(sub_parser)
    tup[0].AddArguments(sub_parser)
    sub_parser.set_defaults(func=tup[0].Run)

  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
  elif len(sys.argv) == 2 and sys.argv[1] in actions:
    parser.parse_args(sys.argv[1:] + ['-h'])
    sys.exit(1)

  args = parser.parse_args()
  logging.basicConfig(level=logging.WARNING - args.verbose * 10,
                      format='%(levelname).1s %(relativeCreated)6d %(message)s')

  if not args.no_pypy and platform.python_implementation() == 'CPython':
    # Switch to pypy if it's available.
    pypy_path = distutils.spawn.find_executable('pypy')
    if pypy_path:
      logging.debug('Switching to pypy.')
      os.execv(pypy_path, [pypy_path] + sys.argv)
    # Running with python: 6s. Running with pypy: 3s
    logging.warning('This script runs more than 2x faster if you install pypy.')

  if logging.getLogger().isEnabledFor(logging.DEBUG):
    atexit.register(_LogPeakRamUsage)

  args.func(args, parser)


if __name__ == '__main__':
  main()
