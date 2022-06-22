# Based on https://github.com/derrod/twl.py
# Original Copyright (c) 2020 Rodney
# The MIT License (MIT)

import os
from getpass import getpass
import requests
import pickle
import browser_cookie3

from TwitchUserChatHistory.constants import GQLOperations, CLIENT_ID, USER_AGENT


class TwitchLogin(object):
    def __init__(self):
        self.session = requests.session()
        self.client_id = CLIENT_ID
        self.session.headers.update({
            'Client-ID': self.client_id,
            'User-Agent': USER_AGENT
        })

        self.username = None
        self.password = None
        self.token = None
        self.user_id = None
        self.cookies_path = None
        self.cookies = []

    def login(self):
        self.username = input(f'Enter your username: ')

        self.set_cookies_path()
        if not self.load_cookies():
            self.set_token(self.cookies['auth-token'])
            self.user_id = self.cookies['persistent']
            print('Found cookies, no login needed')
            return 0

        self.password = getpass('Enter your password: ')

        post_data = {
            'username': self.username,
            'password': self.password,
            'client_id': self.client_id,
            'undelete_user': False,
            'remember_me': True,
        }

        for attempt in range(0, 20):
            response = self.send_login_request(post_data)

            if 'captcha_proof' in response:
                post_data['captcha'] = {'proof': response['captcha_proof']}

            if 'error_code' in response:
                error_code = response['error_code']

                # missing 2fa token from authenticator
                if error_code in [3011, 3012]:
                    if error_code == 3011:
                        print('Two factor authentication enabled')
                    else:
                        print('Invalid two factor token')

                    token_2fa = input("Enter token from authenticator: ")
                    post_data['authy_token'] = token_2fa
                    continue

                # missing verification code from email
                elif error_code in [3022, 3023]:
                    if error_code == 3022:
                        print('Login Verification Code required')
                    else:
                        print('Invalid Login Verification Code')

                    token_2fa = input('Enter 6-digit code from email: ')
                    post_data['twitchguard_code'] = token_2fa
                    continue

                elif error_code in [3001, 3002, 3003]:
                    print('Invalid username or password')

                    self.password = getpass('Enter your password: ')
                    post_data['password'] = self.password
                    continue

                elif error_code == 2005:
                    print('Invalid password length')

                    self.password = getpass('Enter your password: ')
                    post_data['password'] = self.password
                    continue

                elif error_code == 1000:
                    print('Console login unavailable. Captcha solving required')
                    q_login_browser = input('Do you want to login via browser (y / n)? ')
                    if q_login_browser in ['y', 'Y']:
                        cookies_dict = self.get_cookies_browser()
                        if cookies_dict is None:
                            return 3
                        self.set_token(cookies_dict['auth-token'])
                        if self.set_user_id():
                            return 5
                        self.save_cookies(cookies_dict)
                        print('Successfully logged in, cookies saved')
                        return 0
                    return 3

                else:
                    print(f'Unknown error. Error code: {error_code}. Error: {response["error"]}')
                    return 2

            if 'access_token' in response:
                self.set_token(response['access_token'])
                if self.set_user_id():
                    return 5
                cookies_dict = self.session.cookies.get_dict()
                self.save_cookies(cookies_dict)
                print('Successfully logged in, cookies saved')
                return 0

        print('Maximum attempts exceeded')
        return 1

    def send_login_request(self, data_json):
        response = self.session.post('https://passport.twitch.tv/login', json=data_json)
        response_json = response.json()
        return response_json

    def set_token(self, token):
        self.token = token
        self.session.headers.update({'Authorization': f'OAuth {self.token}'})

    def set_user_id(self):
        data_json = GQLOperations.ReportMenuItem.copy()
        data_json['variables'] = {'channelLogin': self.username}
        response = self.session.post(GQLOperations.url, json=data_json)

        if response.status_code != 200:
            return 1
        response_json = response.json()
        if 'data' in response_json and 'user' in response_json['data'] and response_json['data']['user']['id'] is not None:
            self.user_id = response_json['data']['user']['id']
            return 0
        return 2

    def get_cookies_browser(self):
        browser = input('What browser do you use (1 - Chrome / 2 - Chromium / 3 - Firefox / 4 - Opera / 5 - Other)? ')
        if browser not in ('1', '2', '3', '4'):
            print('Browser not supported')
            return None

        input('Login inside browser (NOT incognito mode) and press <enter>')
        twitch_domain = '.twitch.tv'
        try:
            if browser == '1':
                cookie_jar = browser_cookie3.chrome(domain_name=twitch_domain)
            elif browser == '2':
                cookie_jar = browser_cookie3.chromium(domain_name=twitch_domain)
            elif browser == '3':
                cookie_jar = browser_cookie3.firefox(domain_name=twitch_domain)
            elif browser == '4':
                cookie_jar = browser_cookie3.opera(domain_name=twitch_domain)
        except browser_cookie3.BrowserCookieError:
            print('Cannot find cookies')
            return None

        cookies_dict = requests.utils.dict_from_cookiejar(cookie_jar)
        if 'auth-token' not in cookies_dict:
            print('Cannot find required data in cookies')
            return None
        return cookies_dict

    def set_cookies_path(self):
        cookies_dir = os.path.join(os.getcwd(), 'cookies')
        if not os.path.exists(cookies_dir):
            os.mkdir(cookies_dir)
        self.cookies_path = os.path.join(cookies_dir, f'cookies_{self.username}.pkl')

    def save_cookies(self, cookies_dict):
        if 'auth-token' not in cookies_dict:
            cookies_dict['auth-token'] = self.token
        if 'persistent' not in cookies_dict:  # saving user id cookies
            cookies_dict['persistent'] = self.user_id
        self.cookies = cookies_dict.copy()
        pickle.dump(self.cookies, open(self.cookies_path, 'wb'))

    def load_cookies(self):
        if os.path.isfile(self.cookies_path):
            self.cookies = pickle.load(open(self.cookies_path, 'rb'))
            return 0
        return 1
