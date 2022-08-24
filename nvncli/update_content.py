import os
import logging
import time
from nvncli import multihost
from nvncli.multihost import MultiHost

from socketIO_client_nexus import SocketIO, BaseNamespace

from nvncli.spider import Spider
from nvncli.nvn_utils import rawTextToDelta, generateDeleteContent, comparingAndRetainIf

class SocketNamespace(BaseNamespace):
    def on_connect(self):
        print('WSS connected')

    def on_disconnect(self):
        print('WSS disconnected')

    def on_reconnect(self):
        print('WSS reconnected')

class NotevnSocket(SocketIO):

    def __init__(self, url_key, live_server, port = 443):

        self.socket_url = live_server
        self.port = port
        self.url_key = url_key
        self.filepath = ''
        self.file_stamp = 0

        super().__init__(self.socket_url, self.port, SocketNamespace)

        # logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
        # logging.basicConfig()
        
    def join_room(self):
        self.emit('join_room', self.url_key)

    def publish(self, content, cursor_location):
        io_data = dict()

        io_data['name'] = self.url_key
        io_data['text'] = content
        io_data['cursor_location'] = cursor_location

        self.emit('editing', io_data)
        
class Notevn:

    def __init__(self, url_key, live_update=False, multihost=MultiHost('main_note')):
        self.multihost = multihost

        self.url_key = url_key
        self.domain = self.multihost.get_domain_name(True)
        self.spider = Spider(self.domain + self.url_key, multihost=self.multihost)
        self.pad_key = self.spider.pad_key

        # self.tmpContent = self.spider.content
        self.content = self.spider.content
        self.haspw = self.spider.haspw

        self.io = None

        if live_update:
            if self.multihost.is_valid_live_server() == False:
                print('Live update is not available, please try to change mode to "main_note"')
                return
            self.io = NotevnSocket(self.url_key, self.multihost.get_live_server(), port=self.multihost.get_live_port())
            self.io.join_room()


    def get_content_from_file_path(self, file_path):
        content = ''

        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except IOError:
            print('File not found')

        return content


    def is_file_content_changed(self):
        try:
            new_file_stamp = os.stat(self.filepath).st_mtime
        except Exception as _:
            new_file_stamp = 0

        if(new_file_stamp != self.file_stamp):
            return True
        return False


    def save_to_file(self, filename, overwrite):
        with open(filename, 'w') as f:
            f.write(self.content)

        return
                    

    def save_file(self, filepath, overwrite):
        file_content = self.get_content_from_file_path(filepath)

        self.filepath = filepath
        try:
            self.file_stamp = os.stat(filepath).st_mtime
        except Exception as _:
            self.file_stamp = 0

        if(overwrite):
            self.content = file_content
        else:
            self.content += file_content

        if self.io:
            io_content = comparingAndRetainIf(self.content, key = self.pad_key, shared_url=self.multihost.get_shared_url())
            if io_content != None:
                self.io.publish(io_content, len(self.content))

        sub_mode = self.multihost.get_sub_mode()
        data = dict()
        # sub_mode == 'false
        content_to_save = self.content

        if sub_mode == 'main_note':
            content_to_save = rawTextToDelta(self.content)
        elif sub_mode == None:
            print('Invalid sub mode!')
            return

        data['data[0][name]'] = self.url_key
        data['data[0][data]'] = content_to_save
        data['data[0][created_by]'] = 'Vô+danh'
        data['data[0][created_on]'] = int(time.time())
        data['data[0][modified_by]'] = 'Vô+danh'
        data['data[0][modified_on]'] = ''
        data['data[0][visibility]'] = 'true'
        data['data[0][bookmark]'] = 'notevn-cli hackathon'
        data['data[0][slug]'] = self.url_key
        data['data[0][tabid]'] = 'tab_1'
        data['data[0][order_index]'] = '1'
        data['data[0][dummyId]'] = '0'
        data['action'] = 'save'
        data['file'] = '/' + self.url_key
        data['share_url'] = self.pad_key

        self.spider.save(data)

        return

    def view_file(self):
        return self.content

np = None

if __name__ == '__main__':

    np = Notevn('rocktxt', True)