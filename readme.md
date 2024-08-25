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


def convert():
    music_library_sync = MusicLibrarySync(
        source="/mnt/data/music",
        destination="/mnt/data/music-small",
    )
    music_library_sync.remove_wrong_formats()
    music_library_sync.remove_unknown()
    music_library_sync.sync_tags()
    # If you already have a bunch of mp3 files alongside your lossless files, you can
    # copy them over. Or you can convert them as well by not copying them.
    # music_library_sync.copy_missing(match_target_file_extension=True)
    music_library_sync.convert_missing()


def copy_to(destination):
    music_library_sync = MusicLibrarySync(
        source="/mnt/data/music-small",
        destination=destination,
    )
    music_library_sync.remove_unknown()
    music_library_sync.sync_tags()
    music_library_sync.copy_missing(match_target_file_extension=False)


if __name__ == "__main__":
    # First convert it to another directory, making sure everything is of the correct
    # format.
    convert()

    # Then copy it to various other media to avoid redundant conversions, this time
    # not putting any restrictions on the format. Just copy whatever the other steps
    # prepared.
    copy_to("/media/sdcard_1/")
    copy_to("/media/sdcard_2/")
    copy_to("/media/sdcard_3/")

    # Next time this script is run, only new files will be converted and copied.
```

Constructor parameters for the `MusicLibrarySync` class can be used to control the
format. Defaults to mp3 cbr 160kbps, because presumably the vast majority of people
cannot hear higher bitrates than that (I already max out at 128), and because mp3 cbr
is the only format that reliably works everywhere.
