import os
import traceback
import time
from datetime import datetime
from getpass import getpass

from TwitchUserChatHistory.classes.TwitchLogin import TwitchLogin
from TwitchUserChatHistory.classes.TwitchMessagesLog import TwitchMessagesLog


class TwitchUserChatHistory(object):
    def __init__(self):
        self.twitch_login = None
        self.twitch_messages_log = None

    def load_history(self):
        print("""
===~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==
  _______       _ _       _        _    _                   _____ _           _      _    _ _     _                   
 |__   __|     (_) |     | |      | |  | |                 / ____| |         | |    | |  | (_)   | |                  
    | |_      ___| |_ ___| |__    | |  | |___  ___ _ __   | |    | |__   __ _| |_   | |__| |_ ___| |_ ___  _ __ _   _ 
    | \ \ /\ / / | __/ __| '_ \   | |  | / __|/ _ \ '__|  | |    | '_ \ / _` | __|  |  __  | / __| __/ _ \| '__| | | |
    | |\ V  V /| | || (__| | | |  | |__| \__ \  __/ |     | |____| | | | (_| | |_   | |  | | \__ \ || (_) | |  | |_| |
    |_| \_/\_/ |_|\__\___|_| |_|   \____/|___/\___|_|      \_____|_| |_|\__,_|\__|  |_|  |_|_|___/\__\___/|_|   \__, |
                                                                                                                 __/ |
                                                                                                                |___/ 
                                         ___      ___ 
                               _  __    <  /     / _ \\
                              | |/ /    / /     / // /                                               github.com/fyzes
                              |___/    /_/ (_)  \\___/                                                  twitch.tv/fy0d
===~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==~~==
        """)
        print('TwitchUserChatHistory started')

        try:
            self.twitch_login = TwitchLogin()
            if self.twitch_login.login():
                print('Cannot login to twitch')
                input('Press <enter> to exit')
                return 1

            self.twitch_messages_log = TwitchMessagesLog(self.twitch_login.token, self.twitch_login.client_id)
            key_pressed = None
            while key_pressed != '':
                channel_name = input('Enter channel name: ')
                user_name = input('Enter user name: ')
                self.twitch_messages_log.get_history(channel_name, user_name)
                key_pressed = getpass('Press <any key + enter> to load another or <enter> to exit')

        except Exception:
            logs_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(logs_dir):
                os.mkdir(logs_dir)
            logs_path = os.path.join(logs_dir, f'errors_{datetime.now().strftime("%y%m%d_%H%M%S")}.log')
            with open(logs_path, 'w', encoding='utf-8') as logs_file:
                logs_file.write(traceback.format_exc())
            raise

        print('TwitchUserChatHistory ended')
        time.sleep(1)
        return 0
