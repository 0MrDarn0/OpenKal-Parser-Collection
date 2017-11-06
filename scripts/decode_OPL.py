#!/usr/bin/python3.5

import sys
import struct
import json
import utility

def main(path):
    with open(path, 'rb') as stream:
        # Parse
        checksum, map_number, x, y, \
        _, _, _, _, \
        version = struct.unpack('<9I', stream.read(9 * 4))

        if version != 7:
            sys.exit('Only OPL version 7 is supported; is: ' + str(version))

        models = [None] * struct.unpack('<I', stream.read(4))[0]
        for i in range(len(models)):
            models[i] = {
                'path'     : utility.read_string(stream).replace('\\', '/'),
                'position' : utility.read_d3dx_vector3(stream),
                'rotation' : utility.read_d3dx_quaternion(stream),
                'scale'    : utility.read_d3dx_vector3(stream)
            }

        # Verify
        if len(stream.read(1)) != 0:
            sys.exit('Unable to parse OPL, too many bytes')

        # Write,
        json_data = {
            'checksum'      : checksum,
            'coordinate_x'  : x,
            'coordinate_y'  : y,
            'map'           : map_number,
            'version'       : version,
            'models'        : models,
        }

        with open(path + '.json', 'w') as output:
            json.dump(json_data, output,\
                    sort_keys=True, indent=4, separators=(',', ': '))


# Usage: python decode_OPL.py .../n_xxx_yyy.OPL
if __name__ == '__main__':
    main(sys.argv[1])
