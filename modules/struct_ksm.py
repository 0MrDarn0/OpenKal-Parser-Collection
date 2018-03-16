#!/usr/bin/python3.5

import sys
import utility
import numpy as np

from struct import unpack
from utility import ValidationError
from utility import VersionError


class KSMFile(object):
    __slots__ = [
        'area',
    ]

    # Flags used on area['map']
    PORTAL     = 0x1
    TOWN       = 0x2
    SAFE       = 0x4
    CASTLE_ATK = 0x8
    CASTLE_DEF = 0x10

    SIZE = 256

    def parse(self, stream):
        version = unpack('<I', stream.read(4))[0]

        if version != 1:
            raise VersionError('KSM version %d is unsupported' % version)

        try:
            self.area = np.fromstring(stream.read(),
                    [('move', np.uint16), ('zone', np.uint16)])

            self.area.shape = (KSMFile.SIZE, KSMFile.SIZE)

        except (AttributeError, ValueError):
            raise ValidationError('Invalid KSM structure')

        # The move value is interpreted as a boolean
        self.area[self.area['move'] > 0]['move'] = 0xFFFF

        return self

    def write(self, stream):
        raise NotImplementedError


def main(path):
    with open(path, 'rb') as stream:
        try:
            ksm = KSMFile().parse(stream)

        except (VersionError, ValidationError) as e:
            print(str(e) + ' in ' + path)


# Usage: python struct_ksm.py path; performs a parse check, nothing else
if __name__ == '__main__':
    main(sys.argv[1])
