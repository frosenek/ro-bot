from PySide2.QtWidgets import QApplication

import sys
import logging

from robot import Robot


def __init_log__():
    log = logging.getLogger('app')
    log.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    log.addHandler(ch)


if __name__ == "__main__":
    __init_log__()

    app = QApplication(sys.argv)

    robot = Robot(app, 'OriginsRO', 'oriro.exe')

    sys.exit(app.exec_())
