#!/usr/bin/python3.5

import sys
import struct
import argparse

def main(path, key):
    with open('../resources/table_decrypt') as data:
        mapping = [[int(v, 16) for v in line.split()] for line in data]

    outp = path + '.txt'

    with open(path, 'rb') as ifstream, \
         open(outp, 'wb') as ofstream:
        for byte in iter(lambda: ifstream.read(1), b''):
            ofstream.write(struct.pack('<B', mapping[key][ord(byte)]))

# Config: key = 47
# Others: key = 4

# Usage: python decode_DAT.py path key
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('key', type=int)

    args = parser.parse_args()

    if args.key < 0 or args.key > 99:
        parser.error("The key must be in [0, 1, ..., 99]")

    main(args.path, args.key)
