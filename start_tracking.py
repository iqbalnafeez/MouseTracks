"""
This is part of the Mouse Tracks Python application.
Source: https://github.com/Peter92/MouseTracks
"""

from __future__ import absolute_import

from multiprocessing import freeze_support

from core.config import CONFIG
from core.track import start_tracking
from core.os import elevate, tray, launch_new_console


if __name__ == '__main__':
    
    freeze_support()
    
    if CONFIG['Advanced']['RunAsAdministrator']:
        elevate(console=not CONFIG['Main']['StartMinimised'])
    
    #Run normally
    if tray is None or not CONFIG['API']['RunWeb']:
        start_tracking()
    
    #Create tray icon
    else:
        import sys
        from threading import Thread
        
        from generate_images import user_generate
        from core.api import local_address, shutdown_server
        from core.compatibility import Message, input
        from core.internet import get_url_json, send_request
        from core.files import Lock
        from core.notify import *
        from core.sockets import get_free_port
        
        if 'GenerateImages' in sys.argv:
            user_generate()
            
        
        def _end_thread(thread, web_port):
            """Close the tracking thread."""
            if web_port is not None:
                shutdown_server(web_port)
            thread.join()
        
        def _start_tracking(cls, web_port=None, _thread=None):
            """Start new tracking thread after closing old one."""
            #End old thread
            if _thread:
                _end_thread(_thread, web_port)
                NOTIFY(TRACKING_RESTART)
                web_port = None
            
            #Start thread
            web_port = get_free_port() if web_port is None else web_port
            thread = Thread(target=start_tracking, kwargs={'web_port': web_port, 'console': False, 'lock': False})
            thread.start()
        
            #Set new port
            if cls is not None and _thread:
                cls.cache['WebPort'] = web_port
                cls.cache['Thread'] = thread
                cls.set_menu_item('track', name='Pause Tracking')
                if _thread:
                    cls.set_menu_item('restart', kwargs={'web_port': web_port, '_thread': thread})
            return thread

        def toggle_tracking(cls):
            """Pause or resume tracking.
            Add a timeout for if the script crashes.
            """
            web_port = cls.cache['WebPort']
            status_url = '{}/status'.format(local_address(web_port))
            status = get_url_json(status_url, timeout=1)
            
            if status == 'running':
                send_request('{}/stop'.format(status_url), timeout=1, output=True)
            elif status == 'stopped':
                send_request('{}/start'.format(status_url), timeout=1, output=True)
            
        def quit(cls):
            """End the script and close the window."""
            web_port = cls.cache.pop('WebPort')
            thread = cls.cache.pop('Thread')
            _end_thread(thread, web_port)
            tray.quit(cls)
        
        def generate_images(cls):
            launch_new_console(add_arguments=['GenerateImages'], remove_arguments=['Elevate'])
            #user_generate()
        
        def on_menu_open(cls):
            """Run this just before the menu opens."""
            web_port = cls.cache['WebPort']
            status_url = '{}/status'.format(local_address(web_port))
            status = get_url_json(status_url, timeout=0.25)
            
            if status == 'running':
                cls.set_menu_item('track', name='Pause Tracking', hidden=False)
            elif status == 'stopped':
                cls.set_menu_item('track', name='Resume Tracking', hidden=False)
            cls._refresh_menu()
                
        def on_menu_close(cls):
            """Run this after the menu has closed."""
            cls.set_menu_item('track', hidden=True)
        
        def hide_in_tray(cls):
            cls.minimise_to_tray()
        
        def bring_to_front(cls):
            cls.bring_to_front()
            
        def on_hide(cls):
            cls.set_menu_item('hide', hidden=True)
            cls.set_menu_item('restore', hidden=False)
            
        def on_restore(cls):
            cls.set_menu_item('hide', hidden=False)
            cls.set_menu_item('restore', hidden=True)
        
        
        with Lock() as locked:
            if locked:
                web_port = get_free_port()
                thread = _start_tracking(None, web_port)
                menu_options = (
                    {'id': 'generate', 'name': 'Generate Image', 'action': generate_images},
                    {'id': 'track', 'action': toggle_tracking, 'hidden': True},
                    {'id': 'restart', 'name': 'Restart', 'action': _start_tracking, 'kwargs': {'web_port': web_port, '_thread': thread}},
                    {'id': 'hide', 'name': 'Minimise to Tray', 'action': hide_in_tray, 'hidden': bool(CONFIG['Main']['StartMinimised'])},
                    {'id': 'restore', 'name': 'Bring to Front', 'action': bring_to_front, 'hidden': not CONFIG['Main']['StartMinimised']},
                    {'id': 'exit', 'name': 'Quit', 'action': quit},
                )
                t = tray.Tray(menu_options, program_name='Mouse Tracks')
                t.minimise_override = CONFIG['Main']['StartMinimised']
                t.cache['Thread'] = thread
                t.cache['WebPort'] = web_port
                t.set_event('OnMenuOpen', on_menu_open)
                t.set_event('OnMenuClose', on_menu_close)
                t.set_event('OnWindowHide', on_hide)
                t.set_event('OnWindowRestore', on_restore)
                t.listen()
                
            #If start minimised is enabled, this line won't ever be seen, so disable
            elif not CONFIG['Main']['StartMinimised']:
                Message(NOTIFY(PROCESS_NOT_UNIQUE).get_output())
                input()