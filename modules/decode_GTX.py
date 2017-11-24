#!/usr/bin/python3.5

import sys
import struct
import os

def main(path):
    if os.stat(path).st_size < 64:
        sys.exit('Not a valid GTX file')

    with open('../resources/table_decrypt') as data:
        mapping = [[int(v, 16) for v in line.split()] for line in data]

    outp = path + '.dds'

    with open(path, 'rb') as ifstream, \
         open(outp, 'wb') as ofstream:

        # First 8 bytes in DDS are constants
        ifstream.seek(8)

        ofstream.write(struct.pack('<B', ord('D')))
        ofstream.write(struct.pack('<B', ord('D')))
        ofstream.write(struct.pack('<B', ord('S')))
        ofstream.write(struct.pack('<B', ord(' ')))
        ofstream.write(struct.pack('<I', 124))

        # Next 64 bytes in GTX are encrypted
        for i in range(63):
            ofstream.write(struct.pack('<B',
                    mapping[4][ord(ifstream.read(1))]))

        # Copy everything else
        for byte in iter(lambda: ifstream.read(1), b''):
            ofstream.write(byte)

# Usage: python decode_GTX.py path
if __name__ == '__main__':
    main(sys.argv[1])
