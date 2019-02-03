# -*- coding: UTF-8 -*-
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.config import Config
Config.set('kivy', 'window_icon', "KaraoPy256.png")
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '500')
#Config.set('modules', 'monitor', 1)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.properties import DictProperty
from kivy.properties import StringProperty
from kivy.graphics import Rectangle
from kivy.graphics.instructions import InstructionGroup
from pathlib import Path
import win32api
import psutil
import re
from datetime import datetime
import time
from collections import deque
import atexit



with open("filechooserUTF8.kv", encoding='utf-8') as f:
    Builder.load_string(f.read())
    
class InterfaceWidget(FloatLayout):

    last = ''
    back_history = deque([], 10)
    forward_history = deque([], 10)
    current_location = ''
    selected_location = ''
    current_drive = ''
    current_selection = {'index': None, 'location': None}
    current_file_input = ''
    current_list = []
    drives_list = []
    size_prefix = ['K', 'M', 'G', 'T', 'P', 'E', 'Y']
    first_click = True
    double_click_time_limit = 0.3
    gg=StringProperty("aaa")
    b = DictProperty({0: 400, 1:200, 2:100, 3:100})
    type_list = [{'text': 'Pasu file (*.pasu)', 'ext': '.pasu'},
                 {'text': 'All files', 'ext': None}]

    def __init__(self, **kwargs):

        super(InterfaceWidget, self).__init__(**kwargs)
        self.load_drives()   
        self.dropdown = Factory.TypeDropDown()
        filebar = self.search_class(self, 'FileBar')
        self.dropdown_main = filebar.ids['dropdown']
        self.dropdown_main.text = self.type_list[0]['text']
        self.current_ext = self.type_list[0]['ext']
        for i in range(0, len(self.type_list)):
            type_button = Factory.ButtonDropDown()
            type_button.text = self.type_list[i]['text']
            type_button.index = i
            self.dropdown.add_widget(type_button)
        self.receive_path('.')

        #self.fb = self.search_class(self, 'FileBar')

    def update(self, dt):
        #print(self.fb.ids['fileinput'].text)
       #print(self.search_class(self, 'SideBar'))
       pass


    def load_drives(self):
        self.drives = []
        drive_letters = win32api.GetLogicalDriveStrings().split('\x00')
        drive_letters.remove('')
        for letter in drive_letters:
            try:
                name = win32api.GetVolumeInformation(letter)[0]
                self.drives.append([letter.strip('\\'), name])
            except:
                pass
        
        side_bar = self.search_class(self, 'SideBar')

        for drive in self.drives:
            drive_entry = Factory.PartitionEntry()
            side_bar.ids['drives_grid'].add_widget(drive_entry)
            drive.append(drive_entry)
            drive_entry.text = drive[1] + ' (' + drive[0] + ')'
            drive_entry.unit = drive[0]
            
    def search_class(self, current_object, class_to_be_searched):
        for i in range(0, len(current_object.children)):
            class_name = re.search('(?<=\.)[A-z0-9]+(?= )', str(current_object.children[i])).group(0)
            if class_name == class_to_be_searched:
                return current_object.children[i]
            result = self.search_class(current_object.children[i], class_to_be_searched)
            if result != None:    
                return result

    def select_drive(self, instance):
        if instance.state == 'down':
            instance.already_selected = True
            for i in instance.parent.children:
                if i != instance:
                    i.state = 'normal'
                    i.already_selected = False

            self.load_files_list(instance.unit + '\\')
        else:
            if instance.state == 'normal' and instance.already_selected == False:
                instance.state = 'down'
                self.load_files_list(instance.unit + '\\')
        

    def load_files_list(self, path):
        try:
            p = Path(path)
            p = p.resolve()
            self.current_list = []
            listpane = self.search_class(self, 'ListPane')
            listpane.ids['files_list'].clear_widgets()
            j = 0
        except:
            pass

        try:
            for i in p.iterdir():
                if i.suffix == self.current_ext or self.current_ext == None or i.is_dir():
                    entry = Factory.FileEntry()
                    listpane.ids['files_list'].add_widget(entry)
                    entry.ids['name'].text = i.name
                    
                    mtime = datetime.fromtimestamp(i.stat().st_mtime)
                    mtime = mtime.strftime('%Y/%m/%d %H:%M:%S')
                    entry.ids['moddate'].text = str(mtime) 
                    
                    if i.is_dir():
                        entry.ids['size'].text = ''
                        entry.ids['type'].text = 'Folder'
                        for children in entry.children:
                            children.bold = True
                            children.color = [.1, .35, .7, 1]
                        
                    else:
                        size = int(i.stat().st_size / 1024)
                        size = str(size) + ' KB'
                        entry.ids['size'].text = size
                        entry.ids['type'].text = i.suffix[1:]
                    
                    entry.index = j
                    j += 1
                    self.current_list.append(entry)
   
                self.update_error_msg(clear = True)
            self.current_location = p    
            self.update_history(p)
            self.update_path_input(p)
            self.select_drive_internal(p.drive)

        except Exception as e:
            #self.current_location = p.parent
            
            self.load_files_list(self.current_location)  
            if p.is_dir():
                self.update_error_msg(msg = 'This folder cannot be opened.')
            else:
                self.open_file()
                #self.update_error_msg(msg = 'This file cannot be opened.')   
            print(e)     

        finally:
            self.current_selection = {'index': None, 'location': None}
            self.update_file_input(clear = True)
            self.update_nav_button()
            

    def select_drive_internal(self, drive):
        for i in self.drives:
            if str(drive) == i[0]:
                i[2].state = 'down'
            else:
                i[2].state = 'normal'
            i[2].already_selected = False

    def select_file(self, index, state):
        
        if index != self.current_selection['index']:
            
            self.double_click_check(0)
            for i in self.current_list[index].children:
                if state == 'down':
                    i.state = 'down'
                    i.background_normal = 'buttons\\pressed.png'
                    i.background_down = i.background_normal
                else:
                    i.state = 'normal'
                    i.background_normal = 'buttons\\transparency.png'
                    i.background_down = i.background_normal
                
            
            for j in range(0, len(self.current_list)):
                if j != index:
                    for i in self.current_list[j].children:
                        i.state = 'normal'
                        i.background_normal = 'buttons\\transparency.png'
                        i.background_down = i.background_normal
            self.current_selection['index'] = index
            self.current_selection['location'] = self.current_location / self.current_list[index].ids['name'].text
            self.update_file_input()
            #self.first_click = True

        else:
            #self.first_click = False
            if self.double_click_check(1, 10) == True:
                #self.load_files_list(self.current_selection['location'])
                self.open_file()
        

    def update_file_input(self, clear = False):
        filebar = self.search_class(self, 'FileBar')
        fileinput = filebar.ids['fileinput'] 
        if clear == False:            
            fileinput.text = str(self.current_selection['location']).split('\\')[-1]
        else:
            fileinput.text = ''

    def update_path_input(self, path, startup = False):
        navigationbar = self.search_class(self, 'NavigationBar')
        pathinput = navigationbar.ids['pathinput'] 
        pathinput.text = str(path)

    def double_click_check(self, count, time_limit = None):
        if count == 0:
            self.click_time = time.perf_counter()

        elif count == 1 and time_limit != None:
            t = time.perf_counter()
            if t - self.click_time < time_limit:
                return True
            else:
                return False
       
        else:
            raise Exception('No time_limit argument when count = 1')

    def update_error_msg(self, msg = None, clear = False):
        buttonsbar = self.search_class(self, 'ButtonsBar')
        if clear == True:
            buttonsbar.ids['error_msg'].text = ''
        else:
            buttonsbar.ids['error_msg'].text = msg

    def update_nav_button(self):
        navbar = self.search_class(self, 'NavigationBar')

        if len(self.back_history) > 1:
            navbar.ids['back'].disabled = False
        else:
            navbar.ids['back'].disabled = True

        if len(self.forward_history) > 0:
            navbar.ids['forward'].disabled = False
        else:
            navbar.ids['forward'].disabled = True

        if self.current_location != self.current_location.parent:
            navbar.ids['upper'].disabled = False
        else:
            navbar.ids['upper'].disabled = True

    def update_history(self, current):
        if len(self.back_history) < 1 or current != self.back_history[-1]:
            self.back_history.append(current)

    def up(self):
        self.load_files_list(self.current_location.parent)
        

    def back(self):
        last = self.back_history[-2]
        self.forward_history.append(self.back_history.pop())
        self.load_files_list(last)

    def forward(self):
        last = self.forward_history[-1]
        self.back_history.append(self.forward_history.pop())
        self.load_files_list(last)

    def opendropdown(self, instance):
        self.dropdown.open(instance)

    def dropdown_selection(self, index):
        self.dropdown_main.text = self.type_list[index]['text']
        self.current_ext = self.type_list[index]['ext']
        self.dropdown.dismiss()
        self.load_files_list(self.current_location)

    def receive_path(self, path):
        path = path.strip('"')
        if not path.endswith('\\'):
            p = Path(path + '\\')
        else:
            p = Path(path)    

        if not p.exists():
            self.update_error_msg(msg = 'Path may not exist.')
        else:
            self.load_files_list(p)

    def open_file(self):
        # filebar = self.search_class(self, 'FileBar')
        # fileinput = filebar.ids['fileinput'].text
        # path = fileinput.strip('"')

        # if not path.endswith('\\'):
        #     p = Path('.\\' + path + '\\')
        # else:
        #     p = Path(path)
        p = self.current_selection['location']  
        
        if not p.exists():
            self.update_error_msg(msg = 'Path may not exist.')
        elif p.is_dir():
            self.load_files_list(p)
        else:
            self.write_result(p)

    def cancel(self):
        self.write_result('')
        App.get_running_app().stop()
    
    def exit_x(self):
        App.get_running_app().stop()

    def write_result(self, data):
        with open('filechooser_result','w') as f:
            f.write(str(data))
        App.get_running_app().stop()


class filechooserApp(App):

    def build(self):
        self.iw = InterfaceWidget()
        self.title = 'Open file'
        #atexit.register(self.iw.cancel)
        Clock.schedule_once(self.iw.update, 0)
        return self.iw

if __name__ == '__main__':
    filechooserApp().run()
