import logging
import struct
import gzip
import pathlib as pl
import numpy as np

log = logging.getLogger('app.file')

DIRECTORY_MAP_FILES = pl.Path.cwd() / 'assets' / 'map'


class BinaryFile(object):

    def __init__(self, name: str):
        self._filepath = (self.path() / name).with_suffix(self.extension())

    def __repr__(self):
        return str(self._filepath)

    def path(self) -> pl.Path:
        raise NotImplementedError

    def load(self):
        log.debug(f'Loading {self}')
        if not self._filepath.exists():
            log.error(f'File not found: {self}')
            raise FileNotFoundError

        with open(str(self._filepath), 'rb') as file:
            data = self.read(file)
            log.debug(f'Loading successful')
            return data

    def save(self, *args):
        with open(str(self._filepath), 'wb') as file:
            return self.write(file, *args)

    def read(self, file):
        raise NotImplementedError

    def write(self, file, *args):
        raise NotImplementedError

    def extension(self) -> str:
        raise NotImplementedError

    def exists(self) -> bool:
        return self._filepath.exists()


class FieldFile(BinaryFile):

    def __init__(self, name: str):
        super(FieldFile, self).__init__(name)

    def path(self) -> pl.Path:
        return DIRECTORY_MAP_FILES

    def read(self, file):
        buffer = gzip.decompress(file.read())

        header_size = struct.calcsize('2H')
        header, buffer = buffer[:header_size], buffer[header_size:]
        buffer_size = int(len(buffer) / struct.calcsize('B'))

        width, height = struct.unpack('2H', header)
        fld = np.asarray(struct.unpack_from(f'{buffer_size}B', buffer), dtype=np.uint8)

        data = np.zeros((width, height), dtype=np.uint8)
        for x in range(0, width):
            for y in range(0, height):
                data[x, y] = fld[y * width + x]

        return width, height, data

    def write(self, file, *args):
        pass

    def extension(self) -> str:
        return '.fld'
