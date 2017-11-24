#!/usr/bin/python3.5

import sys
import struct
import json

# Reads a ENV7 and writes its sub-components to disk
def main(path):
    with open(path, 'rb') as stream:
        # Parse
        crc, map_number, \
        _, _, _,         \
        _, _, _,         \
        version = struct.unpack('<9I', stream.read(9 * 4))

        if version != 7:
            sys.exit('Only ENV version 7 is supported; is: ' + str(version))

        decals = [None] * struct.unpack('<I', stream.read(4))[0]
        for i in range(len(decals)):
            decals[i] = {
                'index' : struct.unpack('<I', stream.read(4))[0],
                'path' : get_var_string(stream).replace('\\', '/')
            }

        lights = [None] * 24
        for i in range(24):
            k, r, g, b, a = struct.unpack('<I4f', stream.read(20))

            lights[i] = {
                'key' : bool(k),
                'r'   : round(r, 3),
                'g'   : round(g, 3),
                'b'   : round(b, 3),
                'a'   : round(a, 3)
            }

        layers = [None] * struct.unpack('<I', stream.read(4))[0]
        for i in range(len(layers)):
            layers[i] = {
                'scale_u' : struct.unpack('<I', stream.read(4))[0],
                'scale_v' : struct.unpack('<I', stream.read(4))[0],
                'path' : get_var_string(stream).replace('\\', '/')
            }

        # Verify
        if len(stream.read(1)) != 0:
            sys.exit('Unable to parse ENV, too many bytes')

        # Write
        json_data = {
            'decals' : decals,
            'layers' : layers,
            'lights' : lights
        }

        with open(path + '.json', 'w') as output:
            json.dump(json_data, output,\
                    sort_keys=True, indent=4, separators=(',', ': '))

def get_var_string(stream):
    n = struct.unpack('<I', stream.read(4))[0]

    return struct.unpack('%ds' % n,
            stream.read(n))[0].decode("utf-8")

# Usage: python decode_ENV.py path
if __name__ == '__main__':
    main(sys.argv[1])
