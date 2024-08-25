<h1 align="center">💿📂<br/>Music Library Synchronization</h1>
<br/>

Synchronize a directory with music of various formats (flac, mp3, etc.) with one
that contains smaller formats for smaller portable devices.

- Removes music that is either moved or removed from the source folder
- Only spend time converting music that is missing in the destination
- Copy tags from source to destination without converting from scratch
- Copy music with the correct extension to avoid spending time converting

Installation:

```bash
sudo apt install soundconverter python3-mutagen
pip install git+https://github.com/KristoforMaynard/music-tag
pip install git+https://github.com/sezanzeb/music-library-sync
```

Example setup:

```py
#!/usr/bin/env python3
from music_library_sync.music_library_sync import MusicLibrarySync


def sync_small():
    music_library_sync = MusicLibrarySync(
        source="/mnt/data/music",
        destination="/mnt/data/music-small",
    )
    music_library_sync.remove_wrong_formats()
    music_library_sync.remove_unknown()
    music_library_sync.sync_tags()
    music_library_sync.convert_missing()


def sync_sd():
    music_library_sync = MusicLibrarySync(
        source="/mnt/data/music-small",
        destination="/media/sdcard/",
    )
    music_library_sync.remove_wrong_formats()
    music_library_sync.remove_unknown()
    music_library_sync.sync_tags()
    music_library_sync.copy_missing()


if __name__ == "__main__":
    # various setups. First convert it to another directory, and from that directory
    # copy it to various other media to avoid redundant conversions.
    sync_small()
    sync_sd()
    ...
```

Constructor parameters for the `MusicLibrarySync` class can be used to control the
format. Defaults to mp3 cbr 160kbps, because presumably the vast majority of people
cannot hear higher bitrates than that (I already max out at 128), and because mp3 cbr
is the only format that reliably works everywhere.
