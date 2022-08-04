# window.py
#
# Copyright 2022 Pat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Adw, Gio, GLib, Gtk


@Gtk.Template(resource_path='/com/example/TextViewer/window.ui')
class TextViewerWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'TextViewerWindow'

    main_text_view = Gtk.Template.Child()
    open_button = Gtk.Template.Child()
    cursor_pos = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        open_action = Gio.SimpleAction(name='open')
        open_action.connect('activate', self.open_file_dialog)
        self.add_action(open_action)

        save_action = Gio.SimpleAction(name='save-as')
        save_action.connect('activate', self.save_file_dialog)
        self.add_action(save_action)

        buffer = self.main_text_view.get_buffer()
        buffer.connect('notify::cursor-position', self.update_cursor_position)

    def save_file_dialog(self, action, _):
        self._native = Gtk.FileChooserNative(
            title = 'Save File As',
            transient_for = self,
            action = Gtk.FileChooserAction.SAVE,
            accept_label = '_Save',
            cancel_label = '_Cancel',
        )
        self._native.connect('response', self.on_save_response)
        self._native.show()

    def on_save_response(self, native, response):
        if response == Gtk.ResponseType.ACCEPT:
            self.save_file(native.get_file())

        self._native = None

    def save_file(self, file):
        """
        Retrieve the iterators at the start and end of the buffer, and all visible text between the two bounds
        """
        buffer = self.main_text_view.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        text = buffer.get_text(start, end, False)

        if not text:
            return

        bytes = GLib.Bytes.new(text.encode('utf-8'))

        file.replace_contents_bytes_async(
            bytes,
            None,
            False,
            Gio.FileCreateFlags.NONE,
            None,
            self.save_file_complete
        )

    def save_file_complete(self, file, result):
        res = file.replace_contents_finish(result)
        info = file.query_info('standard::display-name', Gio.FileQueryInfoFlags.NONE)

        if info:
            display_name = info.get_attribute_string('standard::display-name')
        else:
            display_name = file.get_basename()

        if not res:
            print(f'Unable to save {display_name}')

    def update_cursor_position(self, buffer, _):
        """
        Retrieve the value of the cursor-position property and contstruct the
        text iterator for the cursor's position.
        """
        cursor_pos = buffer.props.cursor_position
        iter = buffer.get_iter_at_offset(cursor_pos)
        line = iter.get_line() + 1
        column = iter.get_line_offset() + 1

        self.cursor_pos.set_text(f'Ln {line}, Col {column}')

    def open_file_dialog(self, action, parameter):
        """
        Create a new file selection dialog using the "open" mode and keep
        a reference to it.
        """
        self._native = Gtk.FileChooserNative(
            title = 'Open File',
            transient_for = self,
            action = Gtk.FileChooserAction.OPEN,
            accept_label = '_Open',
            cancel_label = '_Cancel',
        )

        """
        Connect the "response" signal of the file selection dialog.
        This signal is emitted when the user selects a file or when they cancel
        the operation.
        """
        self._native.connect('response', self.on_open_response)
        self._native.show()

    def on_open_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            self.open_file(dialog.get_file())

        self._native = None

    def open_file(self, file):
        file.load_contents_async(None, self.open_file_complete)

    def open_file_complete(self, file, result):
        contents = file.load_contents_finish(result)

        info = file.query_info('standard::display-name', Gio.FileQueryInfoFlags.NONE)

        if info:
            display_name = info.get_attribute_string('standard::display-name')
        else:
            display_name = file.fet_basename()

        if not contents[0]:
            path = file.peek_path()
            print(f'Unable to open {path}: {contents[1]}')

        try:
            text = contents[1].decode('utf-8')
        except UnicodeError as err:
            path = file.peek_path()
            print(f"Unable to load the contents of {path}: the file is not encoded with UTF-8")
            return

        buffer = self.main_text_view.get_buffer()
        buffer.set_text(text)
        start = buffer.get_start_iter()
        buffer.place_cursor(start)

        self.set_title(display_name)

class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.props.program_name = 'text-viewer'
        self.props.version = "0.1.0"
        self.props.authors = ['Pat']
        self.props.copyright = '2022 Pat'
        self.props.logo_icon_name = 'com.example.TextViewer'
        self.props.modal = True
        self.set_transient_for(parent)
