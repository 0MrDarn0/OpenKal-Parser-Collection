#!/usr/bin/python3.5

import sys
import utility
import numpy as np

from struct import unpack
from utility import ValidationError
from utility import VersionError


class KCMFile(object):
    __slots__ = [
        'x',
        'y',
        'alpha_ids',
        'decal_ids',
        'alpha_maps',
        'decal_map',
        'color_map',
        'height_map',
    ]

    _SIZE_1 = 256
    _SIZE_2 = 257

    def parse(self, stream):
        _, _,       \
        self.x,     \
        self.y,     \
        _, _, _, _, \
        version = unpack('<9I', stream.read(36))

        if version != 7:
            raise VersionError('KCM version %d is unsupported' % version)

        # Read ids, slice empty (0xFF) positions
        self.alpha_ids = list(unpack('<8B', stream.read(8)))
        self.decal_ids = list(unpack('<8B', stream.read(8)))

        self.alpha_ids.sort()
        self.decal_ids.sort()

        alpha_count = sum(i != 0xFF for i in self.alpha_ids)
        decal_count = sum(i != 0xFF for i in self.decal_ids)

        self.alpha_ids = self.alpha_ids[:alpha_count]
        self.decal_ids = self.decal_ids[:decal_count]

        self.alpha_maps = []
        for _ in range(alpha_count):
            self.alpha_maps.append(
                    np.frombuffer(stream.read(KCMFile._SIZE_1 ** 2), np.uint8))

        self.height_map = np.frombuffer(
                stream.read(2 * KCMFile._SIZE_2 ** 2), np.uint16)

        self.color_map = np.frombuffer(
                stream.read(3 * KCMFile._SIZE_1 ** 2), (np.uint8, 3))

        self.decal_map = np.frombuffer(
                stream.read(KCMFile._SIZE_1 ** 2), np.uint8)

        # Verify
        if stream.read(1):
            raise ValidationError('Too many bytes in KCM structure')

        return self

    def write(self, stream):
        raise NotImplementedError


def main(path):
    with open(path, 'rb') as stream:
        try:
            kcm = KCMFile().parse(stream)

        except (VersionError, ValidationError) as e:
            print(str(e) + ' in ' + path)


# Usage: python struct_kcm.py path; performs a parse check, nothing else
if __name__ == '__main__':
    main(sys.argv[1])
