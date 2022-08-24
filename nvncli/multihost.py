class MultiHost ():
    def __init__ (self, sub_mode):
        self.sub_mode = sub_mode
        
    def socket_protocols (self):
        return {
            'socket.io': {
                'is_http_layer': True,
                'ports': {
                    80: 'http',
                    443: 'https'
                }
            },
            'web_socket': {
                'is_http_layer': None,
                'ports': {
                    8080: 'wss',
                }
            }
        }
        
    def get_socket_protocol (self):
        live_info = self.get_variable('live_info')
        protocol = self.socket_protocols()[live_info['connection']]
        return protocol['ports'][live_info['port']]
    
    def hostVariables (self):
        return {
            # https://api.rqn9.com/data/1.0/textvn/
            'debug': {
                'enabled': True,
                'host': 'debug.notevn.com',
                'note_info': {
                    'available': True,
                    'protocol': 'https',
                    'domain': 'debug.notevn.com',
                    'path': '', # api txt
                    'api_key_required': False, # rqn9 credentials?
                    'method': {
                        'get': 'GET',
                        'save': 'POST',
                        'init': 'POST'
                    },
                    'process_path': '/ajax.php'
                },
                'share_info': { # Incase separate server for share link
                    'available': True,
                    'protocol': 'https',
                    'domain': 'debug.notevn.com',
                    'path': '/raw/',
                    'structure': {
                        'format': 'raw',
                        'type': 'string', # initial type
                        'key': None
                    }
                },
                'live_info': {
                    'available': False,
                    'connection': None,
                    'host': None,
                    'port': -1,
                },
                'formating_options': {
                    'type': 'raw',
                }
            },
            'main_note': {
                'enabled': True,
                'host': 'notevn.com',
                'note_info': {
                    'available': True,
                    'protocol': 'https',
                    'domain': 'notevn.com',
                    'path': '',
                    'api_key_required': False,
                    'method': {
                        'get': 'GET',
                        'save': 'POST',
                        'init': 'POST'
                    },
                    'process_path': '/ajax.php'
                },
                'share_info': {
                    'available': True,
                    'protocol': 'https',
                    'domain': 'notevn.com',
                    'path': '/get_shared/',
                    'structure': {
                        'format': 'json',
                        'type': 'object', # initial type
                        'key': 'ops'
                    }
                },
                'live_info': {
                    'available': True,
                    'connection': 'socket.io',
                    'host': 'live.notevn.com',
                    'port': 443,
                },
                'formating_options': {
                    'type': 'delta',
                }
            },
            'development': {
                'enabled': False, # True,
                'host': 'note.vn.dev',
                'note_info': {
                    'available': True,
                    'protocol': 'http',
                    'domain': 'note.vn.dev',
                    'path': '',
                    'api_key_required': True,
                    'method': {
                        'get': 'GET',
                        'save': 'POST',
                        'init': 'POST'
                    },
                    'process_path': '/save'
                },
                'share_info': {
                    'available': False,
                    'protocol': None,
                    'domain': None,
                    'path': None,
                    'structure': {
                        'format': None,
                        'type': None,
                        'key': None
                    }
                },
                'live_info': {
                    'available': False,
                    'connection': 'socket.io',
                    'host': 'live.note.vn.dev',
                    'port': 80,
                },
                'formating_options': {
                    'type': 'delta',
                }
            }
        }

    def get_sub_mode (self):
        if self.sub_mode == 'debug':
            return 'debug'
        elif self.sub_mode == 'development':
            return 'development'
        elif self.sub_mode == 'main_note' or self.sub_mode == 'production':
            return 'main_note'
        return None

    def get_variable (self, name):
        return self.hostVariables()[self.get_sub_mode()][name]

    def get_domain_name (self, fullPath, lastSlash=True):
        note_info = self.get_variable('note_info')
        return note_info['protocol'] + '://' + note_info['domain'] + (note_info['path'] if fullPath else '') + ('/' if lastSlash else '')

    def get_request_method (self):
        return self.get_variable('note_info')['method']
    
    def get_live_server (self):
        return (self.get_socket_protocol() + '://' + self.get_variable('live_info')['host']) if self.get_variable('live_info')['available'] else None
    
    def is_valid_live_server (self):
        return self.get_variable('live_info')['available']

    def get_live_port (self):
        return self.get_variable('live_info')['port'] if self.get_variable('live_info')['available'] else None

    def get_shared_url (self):
        return self.get_variable('share_info')['protocol'] + '://' + self.get_variable('share_info')['domain'] + self.get_variable('share_info')['path']

    def get_shared_structure (self):
        return self.get_variable('share_info')['structure']

    def get_method_type (self, funcNeed):
        return self.get_variable('note_info')['method'][funcNeed]

    def get_process_url (self):
        return self.get_domain_name(True, lastSlash=False) + self.get_variable('note_info')['process_path']
