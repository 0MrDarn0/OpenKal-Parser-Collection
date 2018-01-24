#!/usr/bin/python3.5

import struct
import argparse
import utility


def main(ipath, opath):
    """Converts a GTX to a DDS"""
    with open(ipath, 'rb') as ifstream:

        # 0x7C204C414B == 'KAL ' + chr(124)
        preamble = struct.unpack('<Q', ifstream.read(8))[0]
        if preamble != 0x7C204C414B:
            raise utility.ValidationError('Not a valid GTX image')

        # Next 64 bytes are encrypted
        data = bytearray(utility.decrypt(4, ifstream.read(64)))

        with open(opath, 'wb') as ofstream:
            ofstream.write(struct.pack('<B', ord('D')))
            ofstream.write(struct.pack('<B', ord('D')))
            ofstream.write(struct.pack('<B', ord('S')))
            ofstream.write(struct.pack('<B', ord(' ')))
            ofstream.write(struct.pack('<I', 124))
            ofstream.write(data)

            # Copy everything else
            for data in iter(lambda: ifstream.read(128 * 1024), b''):
                ofstream.write(data)


if __name__ == '__main__':
    # Usage: python decode_GTX.py input (GTX) output (DDS)
    parser = argparse.ArgumentParser()
    parser.add_argument('ipath', type=str, help='the file to be read')
    parser.add_argument('opath', type=str, help='the file to be written')

    args = parser.parse_args()

    try:
        main(args.ipath, args.opath)

    except utility.ValidationError as e:
        print(str(e) + ' in ' + args.ipath)
