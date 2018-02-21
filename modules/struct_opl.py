#!/usr/bin/python3.5

import sys
import utility

from struct import unpack
from utility import ValidationError
from utility import VersionError


class OPLNode(object):
    __slots__ = [
        'path',
        'position',
        'rotation',
        'scale',
    ]

    def parse(self, stream):
        self.path     = utility.read_string_pre(stream)
        self.position = utility.read_d3dx_vector3(stream)
        self.rotation = utility.read_d3dx_quaternion(stream)
        self.scale    = utility.read_d3dx_vector3(stream)
        return self

    def write(self, stream):
        raise NotImplementedError


class OPLFile(object):
    __slots__ = [
        'nodes',
        'x',
        'y',
    ]

    def parse(self, stream):
        _, _,       \
        self.x,     \
        self.y,     \
        _, _, _, _, \
        version = unpack('<9I', stream.read(36))

        if version != 7:
            raise VersionError('OPL version %d is unsupported' % version)

        self.nodes = []
        for _ in range(unpack('<I', stream.read(4))[0]):
            self.nodes.append(OPLNode().parse(stream))

        # Verify
        if stream.read(1):
            raise ValidationError('Too many bytes in OPL structure')

        return self

    def write(self, stream):
        raise NotImplementedError


def main(path):
    with open(path, 'rb') as stream:
        try:
            opl = OPLFile().parse(stream)

        except (VersionError, ValidationError) as e:
            print(str(e) + ' in ' + path)


# Usage: python struct_opl.py path; performs a parse check, nothing else
if __name__ == '__main__':
    main(sys.argv[1])
