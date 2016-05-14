import os.path
import subprocess
import sys

import typing

class FileHandler():
    def error(self, text: str) -> None:
        raise NotImplementedError

    def prompt(self, text: str) -> None:
        raise NotImplementedError

    def is_modified(self) -> bool:
        raise NotImplementedError

    def post_new(self, filename: str = '') -> None:
        raise NotImplementedError

    def post_save(self, saved_filename: str) -> None:
        raise NotImplementedError

    def write_file(self, filename: str) -> None:
        raise NotImplementedError

    def dirty_window_and_start_in_new_process(self) -> bool:
        raise NotImplementedError


    def request_new_file(self, force: bool = False, filename: str = '') -> None:
        # filename is an optional arg at the end for compatibility purposes
        # (aka if I force it stuff can blow up and I don't want that)
        if filename:
            # Can't open a directory, duh
            if os.path.isdir(filename):
                self.error('Path is a directory and can not be opened!')
                return
            # Quit if the file (or something else) exists
            elif os.path.exists(filename):
                self.error('File already exists, use o to open instead!')
                return
            # Quit if the filename/path doesn't seem to be valid
            elif not os.path.isdir(os.path.dirname(filename)):
                self.error('Invalid path')
                return
            else:
                success = self.new_file(force, filename=filename)
        else:
            success = self.new_file(force)
        if not success:
            self.error('Unsaved changes! Force new with n! or save first.')


    def request_open_file(self, filename: str, force: bool = False) -> None:
        if not os.path.isfile(filename):
            self.error('File not found!')
            return
        if self.dirty_window_and_start_in_new_process():
            subprocess.Popen([sys.executable, sys.argv[0], filename])
        elif not self.is_modified() or force:
            success = self.open_file(filename)
            if not success:
                self.error('File could not be opened!')
        else:
            self.error('Unsaved changes! Force open with o! or save first.')


    def request_save_file(self, filename: str = '', force: bool = False) -> None:
        if not filename:
            # Don't save if there's nothing to save
            if not self.is_modified():
                return
            if self.file_path: # type: ignore
                result = self.save_file()
                if not result:
                    self.error('File not saved! IOError!')
            else:
                self.error('No filename')
                self.prompt('s ')
        else:
            if os.path.isfile(filename) and not force:
                self.error('File already exists, use s! to overwrite')
            # Make sure the parent directory actually exists
            elif os.path.isdir(os.path.dirname(filename)):
                result = self.save_file(filename)
                if not result:
                    self.error('File not saved! IOError!')
            # If the file doesn't exist and the path doesn't include a dir, ragequit
            else:
                self.error('Invalid path')


    def new_file(self, force: bool = False, filename: str = '') -> bool:
        """
        Main new file function

        Return True on success, return False if failed
        """
        if self.dirty_window_and_start_in_new_process():
            subprocess.Popen([sys.executable, sys.argv[0]] + ([filename] if filename else []))
            return True
        elif not self.is_modified() or force:
            if filename:
                self.post_new(filename=filename)
            else:
                # For compatibility purposes ugh
                self.post_new()
            return True
        else:
            return False


    def open_file(self, filename: str) -> bool:
        """
        Main open file function

        Return True on success, return False if failed
        """
        raise NotImplementedError


    def save_file(self, filename: str = '') -> bool:
        """
        Main save file function

        Save the file with the specified filename.
        If no filename is provided, save the file with the existing filename,
        (aka don't save as, just save normally)
        """
        if filename:
            saved_filename = filename
        else:
            saved_filename = self.file_path # type: ignore

        assert saved_filename.strip() != ''

        try:
            self.write_file(saved_filename)
        except IOError as e:
            print(e)
            return False
        else:
            self.post_save(saved_filename)
            return True
