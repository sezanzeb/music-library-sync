import os
import re
import glob
from typing import Optional
import music_tag
import shutil

from music_library_sync.logger import logger


class MusicLibrarySync:
    """Synchronize a directory with music with one that contains smaller formats
    efficiently, for example for portable devices with less storage capacity.
    - Removes files that are either moved or removed from the source folder
    - Copy tags from source to destination without converting from scratch
    - Only spend time converting files that are missing in the destination
    """

    def __init__(
        self,
        source: str,
        destination: str,
        soundconverter_format_options: str = "--format mp3 --mode cbr --quality 160",
        target_file_extension: str = "mp3",
        interactive_delete: bool = True,
    ) -> None:
        """file_extension and soundconverter_format_options have to match!"""
        self.source = source
        self.destination = destination

        self.interactive_delete = interactive_delete

        # mp3 cbr is the only format reliably supported everywhere. what a fucking
        # embarrassment.
        # 128 kbps mp3 is already transparent for many people, I'd go with 160, just to
        # be on the safe side.
        self.soundconverter_format_options = soundconverter_format_options
        if target_file_extension.startswith("."):
            target_file_extension = target_file_extension[1:]
        target_file_extension = target_file_extension.lower()
        assert target_file_extension in soundconverter_format_options
        self.target_file_extension = target_file_extension.lower()

    def convert_missing(self) -> None:
        """Convert missing files from the source to the destination."""
        # save time by skipping existing files.

        cpu_count = os.cpu_count() or 1

        command = (
            f"soundconverter -b {self.source}/* "
            f"{self.soundconverter_format_options} "
            "--recursive "
            "--existing skip "
            f"--jobs {max(cpu_count - 2, 1)} "
            f"--output {self.destination}"
        )

        logger.info("running %s", command)
        os.system(command)

    def copy_missing(self, match_target_file_extension: bool = True) -> None:
        """Copy new files from the source to the destination, if they are already of
        the correct file extension.

        Can be used before calling .convert, to save cpu time. If you want to have
        mp3 files in your destination, and if your source directory already contains
        some mp3 files, and you are fine with copying then without converting them
        according to soundconverter_format_options, then use this function.
        """
        for current_folder, subfolders, filenames in os.walk(self.source):
            for filename in filenames:
                input_path = os.path.join(current_folder, filename)

                if not self._should_handle(input_path):
                    continue

                if self.target_file_extension and match_target_file_extension:
                    extension = os.path.splitext(input_path)[1][1:]
                    if extension.lower() != self.target_file_extension.lower():
                        # only copy files that match self.target_file_extension
                        continue

                output_path = os.path.join(
                    self.destination,
                    re.sub(f"^{self.source}/?", "", input_path),
                )

                if os.path.exists(output_path):
                    continue

                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copyfile(input_path, output_path)
                logger.info('Copied "%s" to "%s"', input_path, output_path)

    def remove_wrong_formats(self) -> None:
        """Remove formats from the destination directory that are not of the desired."""
        # Ignoring the file extension, remove anything that is not in the source directory
        files_to_delete = []

        for current_folder, subfolders, filenames in os.walk(self.destination):
            for filename in filenames:
                path = os.path.join(current_folder, filename)

                if not self._should_handle(path):
                    continue

                if not path.lower().endswith(f".{self.target_file_extension.lower()}"):
                    files_to_delete.append(path)

        logger.info(
            "Identified %d non-%s files to delete",
            len(files_to_delete),
            self.target_file_extension,
        )

        if len(files_to_delete) == 0:
            return

        logger.info("Sample: %s", files_to_delete[:5])

        if self.interactive_delete:
            answer = input("Delete them? y/n ")
            if answer != "y":
                return

        for file_to_delete in files_to_delete:
            os.unlink(file_to_delete)

        logger.info("Deleted files")

    def sync_tags(self) -> None:
        """Make sure that the files tags are correct."""
        for current_folder, subfolders, filenames in os.walk(self.destination):
            for filename in filenames:
                converted_path = os.path.join(current_folder, filename)

                if not self._should_handle(converted_path):
                    continue

                try:
                    self._sync_tags_of_file(converted_path)
                except:
                    pass

    def remove_unknown(self) -> None:
        """Remove files that aren't present in the source directory."""
        # Ignoring the file extension, remove anything that is not in the source directory
        files_to_delete = []

        for current_folder, subfolders, filenames in os.walk(self.destination):
            for filename in filenames:
                converted_path = os.path.join(current_folder, filename)

                if not self._should_handle(converted_path):
                    continue

                matching_input_file = self._figure_out_input_path(converted_path)

                if matching_input_file is None:
                    # there is no input for this output
                    files_to_delete.append(converted_path)

        logger.info("Identified %s files that can be deleted", len(files_to_delete))

        if len(files_to_delete) == 0:
            return

        logger.info("Sample: %s", files_to_delete[:5])

        if self.interactive_delete:
            answer = input("Delete them? y/n ")
            if answer != "y":
                return

        for file_to_delete in files_to_delete:
            os.unlink(file_to_delete)

        logger.info("Deleted files")

    def _sync_tags_of_file(self, converted_path: str) -> None:
        """Make sure that the files tags are correct."""
        input_path = self._figure_out_input_path(converted_path)

        input_file = music_tag.load_file(input_path)
        if input_file is None:
            return

        converted_file = music_tag.load_file(converted_path)
        if converted_file is None:
            return

        # TODO might want to iterate over all tags instead
        important_tags = ["genre", "title", "artist", "album", "tracknumber"]
        changed = False
        for important_tag in important_tags:
            if str(input_file[important_tag]) == str(converted_file[important_tag]):
                continue

            changed = True

            converted_file[important_tag] = input_file[important_tag]

        if changed:
            converted_file.save()
            logger.info(f'Updated tags of "%s"', converted_path)

    def _figure_out_input_path(self, converted_path: str) -> Optional[str]:
        """For a given already-existing converted file, find the original file."""
        converted_path_without_ext = os.path.splitext(converted_path)[0]
        converted_path_without_ext_relative = re.sub(
            f"^{self.destination}/?", "", converted_path_without_ext
        )
        input_path_without_ext = os.path.join(
            self.source, converted_path_without_ext_relative
        )
        matching_input_files = glob.glob(f"{glob.escape(input_path_without_ext)}*")

        if len(matching_input_files) == 0:
            return None

        # should usually only be one file
        # try to find a lossless file
        for input_file in matching_input_files:
            extension = os.path.splitext(input_file)[0]
            if extension.lower() in ["flac", "alac", "aiff", "dsd", "mqa", "wav"]:
                return input_file

        # otherwise return any
        return matching_input_files[0]

    def _should_handle(self, path: str):
        # I have this script in my music folder, deal with it
        if "/.idea" in path:
            return False

        if "/.mypy_cache" in path:
            return False

        if path.lower().endswith(".py") or path.lower().endswith(".md"):
            # don't delete this script
            return False

        return True
