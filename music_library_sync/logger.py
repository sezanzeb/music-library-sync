#!/usr/bin/env python3
import logging
import sys


logger = logging.getLogger("MusicLibrarySync")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
