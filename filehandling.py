import os.path
import subprocess
import sys


class FileHandler():
    def error(self, text):
        raise NotImplementedError

    def prompt(self, text):
        raise NotImplementedError

    def is_modified(self):
        raise NotImplementedError

    def post_new(self):
        raise NotImplementedError

    def post_save(self, saved_filename):
        raise NotImplementedError

    def write_file(self, filename):
        raise NotImplementedError

    def dirty_window_and_start_in_new_process(self):
        raise NotImplementedError


    def request_new_file(self, force=False):
        success = self.new_file(force)
        if not success:
            self.error('Unsaved changes! Force new with n! or save first.')


    def request_open_file(self, filename, force=False):
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


    def request_save_file(self, filename='', force=False):
        if not filename:
            # Don't save if there's nothing to save
            if not self.is_modified():
                return
            if self.file_path:
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
            else:
                self.error('Invalid path')


    def new_file(self, force=False):
        """
        Main new file function

        Return True on success, return False if failed
        """
        if self.dirty_window_and_start_in_new_process():
            subprocess.Popen([sys.executable, sys.argv[0]])
            return True
        elif not self.is_modified() or force:
            self.post_new()
            return True
        else:
            return False


    def open_file(self, filename):
        """
        Main open file function

        Return True on success, return False if failed
        """
        raise NotImplementedError


    def save_file(self, filename=''):
        """
        Main save file function

        Save the file with the specified filename.
        If no filename is provided, save the file with the existing filename,
        (aka don't save as, just save normally)
        """
        if filename:
            saved_filename = filename
        else:
            saved_filename = self.file_path

        assert saved_filename.strip() != ''

        try:
            self.write_file(saved_filename)
        except IOError as e:
            print(e)
            return False
        else:
            self.post_save(saved_filename)
            return True
