# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Andrew Starr-Bochicchio <a.starr.b@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

from locale import gettext as _

from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import WebKit
import itertools, re, glob
import logging
logger = logging.getLogger('google_webfont_downloader')

from google_webfont_downloader_lib import Window
from google_webfont_downloader.AboutGoogleWebfontDownloaderDialog import AboutGoogleWebfontDownloaderDialog
from google_webfont_downloader.FindFonts import FindFonts
from google_webfont_downloader_lib.xdg import fontDir
from google_webfont_downloader.DownloadFont import DownloadFont, UninstallFont
from  google_webfont_downloader.html_preview import html_font_view, internet_on, select_text_preview

# See google_webfont_downloader_lib.Window.py for more details about how this class works
class GoogleWebfontDownloaderWindow(Window):
    __gtype_name__ = "GoogleWebfontDownloaderWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        self.fonts = FindFonts()
        """Set up the main window"""
        super(GoogleWebfontDownloaderWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutGoogleWebfontDownloaderDialog
#        self.PreferencesDialog = PreferencesGoogleWebfontDownloaderDialog

        # Code for other initialization actions should be added here.
        self.toolbar = builder.get_object("toolbar")
        context = self.toolbar.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        self.view = WebKit.WebView()
        webview = builder.get_object("webview")
        webview.add(self.view)
        htmlfile = html_font_view()
        self.view.load_html_string(htmlfile, "file:///")
        webview.show_all()

        webview_settings = self.view.get_settings()
        webview_settings.set_property('enable-default-context-menu', False)

        # the data in the model
        listmodel = builder.get_object("liststore")
        # append the values in the model
        for i in range(len(self.fonts)):
            listmodel.append(self.fonts[i])

        # a treeview to see the data stored in the model
        self.listview = builder.get_object("font_list")
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_("Fonts"), cell, text=0)
        self.listview.append_column(col)
        self.listview.columns_autosize()
        # when a row is selected, it emits a signal
        self.listview.get_selection().connect("changed", self.on_select_changed)

        self.search_field = self.builder.get_object('search_field')
        completion = self.builder.get_object('entrycompletion')
        completion.set_model(listmodel)
        completion.set_text_column(0)
        self.search_field.set_completion(completion)
        completion.connect('match-selected', self.on_match_selected)

        self.mnu_save = self.builder.get_object('mnu_save')
        self.mnu_save.connect("activate", self.on_download_btn_clicked)

        self.text_selector = self.builder.get_object('text_selector')
        self.text_menu = self.builder.get_object('text_menu')
        self.text_selector.set_menu(self.text_menu)

        self.r1 = self.builder.get_object('r1')
        self.r2 = self.builder.get_object('r2')
        self.r3 = self.builder.get_object('r3')
        self.r4 = self.builder.get_object('r4')
        self.r5 = self.builder.get_object('r5')
        self.r6 = self.builder.get_object('r6')
        self.r7 = self.builder.get_object('r7')
        self.r8 = self.builder.get_object('r8')
        self.r1.connect("toggled", self.on_menu_choices_changed, "1")
        self.r2.connect("toggled", self.on_menu_choices_changed, "2")
        self.r3.connect("toggled", self.on_menu_choices_changed, "3")
        self.r4.connect("toggled", self.on_menu_choices_changed, "4")
        self.r5.connect("toggled", self.on_menu_choices_changed, "5")
        self.r6.connect("toggled", self.on_menu_choices_changed, "6")
        self.r7.connect("toggled", self.on_menu_choices_changed, "7")
        self.r8.connect("toggled", self.on_menu_choices_changed, "8")
        self.text_content = "random"

    def on_menu_choices_changed(self, button, name):
        if name == "1":
            self.text_content = "random"
        elif name == "2":
            self.text_content = "ipsum"
        elif name == "3":
            self.text_content = "kafka"
        elif name == "4":
            self.text_content = "hgg"
        elif name == "5":
            self.text_content = "ggm"
        elif name == "6":
            self.text_content = "ralph"
        elif name == "7":
            self.text_content = "jj"
        elif name == "8":
            self.text_content = "custom"
        self.set_text()

    def set_text(self):
        t = select_text_preview(self.text_content)
        js_text = "document.getElementById('text_preview').innerHTML = '%s';" % t
        self.view.execute_script(js_text)

    def js_exec(self):
        js_code = ["document.getElementById('start_page').style.display = 'None';",
                   "document.getElementById('text_preview').style.fontFamily = '%s';" % (self.font)]
        if internet_on() == True:
            font_loader = """WebFontConfig = {
            google: { families: [ '%s' ] }
          }; 
          (function() {
            document.getElementsByTagName("html")[0].setAttribute("class","wf-loading")
            document.getElementsByTagName("html")[0].setAttribute("className","wf-loading")
            var wf = document.createElement('script');
            wf.src = ('https:' == document.location.protocol ? 'https' : 'http') +
                '://ajax.googleapis.com/ajax/libs/webfont/1/webfont.js';
            wf.type = 'text/javascript';
            wf.async = 'true';
            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(wf, s);
          })();""" % (self.font)
            show_text = [font_loader,
                         "document.getElementById('no_connect').style.display = 'None';",
                         "document.getElementById('text_preview').style.display = 'block';"]
            js_code.extend(show_text)
            if self.text_content == "random":
                self.set_text()
            for js in js_code:
                self.view.execute_script(js)
            self.js_installed_check()
        else:
            show_no_connect = ["document.getElementById('text_preview').style.display = 'None';",
                               "document.getElementById('no_connect').style.display = 'block';"]
            js_code.extend(show_no_connect)
            for js in js_code:
                self.view.execute_script(js)

    def js_installed_check(self):
        if glob.glob(fontDir + self.font + '.*'):
            js_show = "document.getElementById('installed').style.display = 'block';"
            self.view.execute_script(js_show)
        else:
            js_hide = "document.getElementById('installed').style.display = 'None';"
            self.view.execute_script(js_hide)

    def on_search_field_activate(self, widget):
        fonts = list(itertools.chain(*self.fonts))
        entered_text = self.search_field.get_text()
        matcher = re.compile(entered_text, re.IGNORECASE)
        if any(itertools.ifilter(matcher.match, fonts)):
            for position, item in enumerate(fonts):
                if item.lower() == entered_text.lower():
                    self.listview.set_cursor(position)
        else:
            pass

    def on_match_selected(self, completion, treemodel, treeiter):
        self.font = treemodel[treeiter][completion.get_text_column()]
        self.js_exec()

    def on_select_changed(self, selection):
        (model, iter) =  selection.get_selected()
        self.font = model[iter][0]
        self.js_exec()

    def on_search_field_icon_press(self, widget, icon_pos, event):
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            self.search_field.set_text("")

    def on_download_btn_clicked(self, button):
        try:
            DownloadFont(self.font, uri=None)
            self.js_installed_check()
        except AttributeError:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK, _("This the install button."))
            dialog.format_secondary_text(
                _("Select a font on the left and press this button. \nThe font will be installed for off-line use."))
            dialog.set_modal(True)
            dialog.run()
            dialog.destroy()

    def on_uninstall_btn_clicked(self, button):
        try:
            UninstallFont(self.font)
            self.js_installed_check()
        except AttributeError:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK, _("This the uninstall button."))
            dialog.format_secondary_text(
                _("Select a font on the left and press this button. \nIt will be removed from your system."))
            dialog.set_modal(True)
            dialog.run()
            dialog.destroy()

    def on_info_btn_clicked(self, button):
        try:
            info_url = "http://www.google.com/webfonts/specimen/" + \
                       self.font.replace(' ', '+', -1)
            Gtk.show_uri(None, info_url, 0)
        except AttributeError:
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK, _("This the info button."))
            dialog.format_secondary_text(
                _("Select a font on the left and press this button. \nA browser will open with further information \nabout the chosen font."))
            dialog.set_modal(True)
            dialog.run()
            dialog.destroy()

    def on_mnu_save_as_activate(self, button):
        try:
            dialog = Gtk.FileChooserDialog("Please choose a file", self,
                                           Gtk.FileChooserAction.SAVE,
                                          (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                           Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
            filename = self.font + ".ttf"
            dialog.set_current_name(filename)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                uri = dialog.get_filename()
                DownloadFont(self.font, uri)
            elif response == Gtk.ResponseType.CANCEL:
                pass
            dialog.destroy()
        except AttributeError:
            pass

