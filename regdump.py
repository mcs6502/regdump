#!/usr/bin/env python

"""regdump.py: Display the contents of a registry hive to standard output."""

import argparse
import encodings.hex_codec
import re

from Registry import Registry

__author__ = "Igor Mironov"
__copyright__ = "Copyright 2016, Igor Mironov"
__license__ = "Apache v2.0"


def hex_encode(data):
    return encodings.hex_codec.hex_encode(data)[0]


def as_string(value):
    return value if isinstance(value, basestring) else str(value)


def print_key(key):
    print "%s %s" % (key.timestamp(), key.path().encode('utf-8'))


class RegDump(object):
    def __init__(self, subject):
        self.subject = subject
        self.exclude = None
        self.brief = False
        self.max_depth = 0

    def dump_key(self, key, depth=0):
        if self.max_depth and depth > self.max_depth:
            return
        key_name = key.name()
        # do not evaluate sub-keys or values if this key is excluded
        if self.exclude and self.exclude.match(key_name):
            return
        key_printed = False
        if self.subject.search(key_name):
            print_key(key)
            key_printed = True
        if not self.brief:
            self.dump_values(key, key_printed)
        depth += 1
        if not self.max_depth or depth <= self.max_depth:
            for sub_key in key.subkeys():
                self.dump_key(sub_key, depth)

    def dump_values(self, key, key_printed):
        for v in key.values():
            vn = v.name().encode('utf-8')
            vt = v.value_type()
            vts = v.value_type_str()
            is_binary = \
                vt == Registry.RegBin or \
                vt == Registry.RegResourceRequirementsList or \
                vt == Registry.RegResourceList
            value = v.value()
            vs = hex_encode(value) if is_binary else as_string(value)
            if self.subject.search(vn) or self.subject.search(vs):
                # do not print the value if its name or contents is excluded
                if self.exclude and (self.exclude.match(vn)
                                     or self.exclude.match(vs)):
                    continue
                if not key_printed:
                    print_key(key)
                    key_printed = True
                print "    %s = %s %s" % (repr(vn), vts, repr(vs))

    def set_exclude(self, exclude):
        self.exclude = exclude

    def set_brief(self, brief):
        self.brief = brief

    def set_max_depth(self, max_depth):
        self.max_depth = max_depth


def process_args(cmd_args):
    no_case = re.IGNORECASE
    subject = re.compile(cmd_args.subject if cmd_args.subject else "", no_case)
    reg_dump = RegDump(subject)
    if cmd_args.exclude:
        exclude = re.compile(cmd_args.exclude, re.VERBOSE)
        reg_dump.set_exclude(exclude)
    if cmd_args.brief:
        reg_dump.set_brief(True)
    if cmd_args.max_depth:
        reg_dump.set_max_depth(cmd_args.max_depth)
    with open(cmd_args.hive, "rb") as f:
        r = Registry.Registry(f)
    if not cmd_args.paths:
        keys = [r.root()]
    else:
        keys = map(lambda path: open_key(r, path), cmd_args.paths)
    for key in keys:
        reg_dump.dump_key(key)


def open_key(r, path):
    # strip any leading backslashes as they cause the open() call to fail
    # (it is also safe to remove all trailing backslashes)
    return r.open(path.strip('\\'))


def main():
    parser = argparse.ArgumentParser(
        description='Dump registry hive file to standard output.')
    parser.add_argument('-s', '--subject', metavar='REGEX',
                        help='filter for names and values to display')
    parser.add_argument('-e', '--exclude', metavar='REGEX',
                        help='filter for names and values to omit')
    parser.add_argument('-b', '--brief', action='store_true',
                        help='omit all values')
    parser.add_argument('--max-depth', metavar='N', type=int,
                        help='maximum nesting depth for registry keys')
    parser.add_argument('hive', metavar='FILE', help='input file')
    parser.add_argument('paths', metavar='KEY', nargs='*',
                        help='full path of registry key to search for')
    cmd_args = parser.parse_args()
    process_args(cmd_args)


if __name__ == '__main__':
    main()
