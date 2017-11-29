#!/usr/bin/python3.5

import argparse
import utility


def main(ipath, opath, key):
    with open(ipath, 'rb') as ifstream, \
            open(opath, 'wb') as ofstream:

        for data in iter(lambda: ifstream.read(128 * 1024), b''):
            ofstream.write(bytearray(utility.decrypt(key, data)))


if __name__ == '__main__':
    # Usage: python decode_GTX.py key input (DAT) output (TXT)
    parser = argparse.ArgumentParser()

    # Config: key = 47
    # Others: key = 4
    parser.add_argument('key', type=int)

    parser.add_argument('ipath', type=str, help='the file to be read')
    parser.add_argument('opath', type=str, help='the file to be written')

    args = parser.parse_args()

    if args.key < 0 or args.key > 99:
        parser.error('The key must be in [0, 1, ..., 99]')

    main(args.ipath, args.opath, args.key)
