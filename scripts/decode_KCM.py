#!/usr/bin/python3.5

import sys
import struct
import json

from PIL import Image

SIZE_1 = 256 * 256
SIZE_2 = 257 * 257

# Reads a KCM7 map and writes its sub-components to disk
def main(path):
    with open(path, 'rb') as stream:
        # Parse
        crc, map_number, \
        x_coordinate,    \
        y_coordinate,    \
        _, _, _, _,      \
        version = struct.unpack('<IIIIIIIII', stream.read(9 * 4))

        if version != 7:
            sys.exit("Only KCM version 7 is supported; is: " + str(version))

        alpha_info = struct.unpack('BBBBBBBB', stream.read(8))
        decal_info = struct.unpack('BBBBBBBB', stream.read(8))

        # Skip 1. alpha map index

        alphas = [None] * 7
        for i, _ in enumerate(alphas):
            if alpha_info[i + 1] != 0xFF:
                alphas[i] = read_alpha_map(stream)

        height = read_height_map(stream)

        color = read_color_map(stream)
        decal = read_decal_map(stream)

        # Verify
        if len(stream.read(1)) != 0:
            sys.exit('Unable to parse KCM, too many bytes')

        # Write
        for i, _ in enumerate(alphas):
            if alphas[i] != None:
                write_png(alphas[i], path + ".aplha-" + str(i))

        write_png(height, path + ".height", mode = 'I')

        # Most applications cannot interpret 16-bit grayscale
        # PNGs, which is why a raw format is exported as well

        write_raw_height(height, path + ".height.raw")

        write_png(color, path + ".color", mode = 'RGB')
        write_png(decal, path + ".decal")

        json_data = {
            'checksum'     : crc,
            'coordinate_x' : x_coordinate,
            'coordiante-y' : y_coordinate,
            'map'          : map_number,
            'maps_alpha'   : alpha_info,
            'maps_decal'   : decal_info,
            'version'      : version
        }

        with open(path + '.json', 'w') as output:
            json.dump(json_data, output,\
                    sort_keys=True, indent=4, separators=(',', ': '))

def read_alpha_map(stream):
    return [struct.unpack('<B', stream.read(1))[0] for _ in range(0, SIZE_1)]

def read_decal_map(stream):
    return [struct.unpack('<B', stream.read(1))[0] for _ in range(0, SIZE_1)]

def read_height_map(stream):
    return [struct.unpack('<H', stream.read(2))[0] for _ in range(0, SIZE_2)]

def read_color_map(stream):
    return [struct.unpack('BBB', stream.read(3)) for _ in range(0, SIZE_1)]

def write_raw_height(raw, path):
    with open(path, 'wb') as output:
        for v in raw:
            output.write(struct.pack('>H', v))

def write_png(raw, path, mode = 'L'):
    if len(raw) == SIZE_1:
        size = (256, 256)
    else:
        size = (257, 257)

    im = Image.new(mode, size)
    im.putdata(raw)

    im.transpose(Image.FLIP_TOP_BOTTOM).save(path + ".png", "PNG")

# Usage: python decode_KCM.py .../n_xxx_yyy.kcm
if __name__ == '__main__':
    main(sys.argv[1])
