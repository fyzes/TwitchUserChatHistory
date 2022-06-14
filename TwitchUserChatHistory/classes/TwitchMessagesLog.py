import os
import requests

from TwitchUserChatHistory.constants import GQLOperations


class TwitchMessagesLog(object):
    def __init__(self, token, client_id):
        self.session = requests.session()
        self.token = token
        self.client_id = client_id
        self.session.headers.update({
            'Client-ID': self.client_id,
            'Authorization': f'OAuth {self.token}'
        })

        self.channel_name = None
        self.user_name = None
        self.user_id = None

        self.req_cursor = None
        self.req_messages_list = []
        self.messages_num = 0

        self.data_messages_path = None
        self.data_messages_extra_nodes_path = None

    def get_history(self, channel_name, user_name):
        self.channel_name = channel_name
        self.user_name = user_name
        self.req_cursor = None
        self.req_messages_list.clear()
        self.messages_num = 0
        self.data_messages_path = None
        self.data_messages_extra_nodes_path = None

        ret_value, _ = self.get_user_id(self.channel_name)
        if ret_value == 1:
            print('Cannot get channel id')
            return 11
        elif ret_value == 2:
            print('Channel not exist')
            return 12

        ret_value, self.user_id = self.get_user_id(self.user_name)
        if ret_value == 1:
            print('Cannot get user id')
            return 13
        elif ret_value == 2:
            print('User not exist')
            return 14

        ret_value = self.get_history_req()
        if ret_value == 1:
            print('Cannot get user chat history')
            return 1
        elif ret_value == 2:
            print('You are not moderator on channel')
            return 2
        elif ret_value == 3:
            print('User does not have messages on channel')
            return 3

        self.set_data_path()
        data_messages_file = open(self.data_messages_path, 'w', encoding='utf-8')
        data_messages_extra_nodes_file = open(self.data_messages_extra_nodes_path, 'a', encoding='utf-8')

        while len(self.req_messages_list):
            for message in self.req_messages_list:
                self.req_cursor = message['cursor']
                if message['type'] == 0:
                    data_messages_file.write('[ ' + message['time'] + ' ]  ' + message['user'] + ':  ' + message['text'] + '\n')
                elif message['type'] == 2:
                    data_messages_extra_nodes_file.write('action: ' + message['text'] + '\n')
                elif message['type'] == 3:
                    data_messages_extra_nodes_file.write('category: ' + message['text'] + '\n')
            print(f'\rMessages loaded: {self.messages_num}', end='')
            if self.get_history_req():
                return 2
        print(f'\rMessages loaded: {self.messages_num}')

        data_messages_file.close()
        data_messages_extra_nodes_file.close()
        return 0

    def get_history_req(self):
        data_json = GQLOperations.ViewerCardModLogsMessagesBySender.copy()
        data_json['variables'] = {
            'senderID': self.user_id,
            'channelLogin': self.channel_name
        }
        self.req_messages_list.clear()
        if self.req_cursor:
            data_json['variables']['cursor'] = self.req_cursor

        response = self.session.post(GQLOperations.url, json=data_json)
        if response.status_code != 200:
            return 1
        response_json = response.json()

        if response_json['data']['channel']['modLogs']['messagesBySender'] is None:
            return 2  # user is not moderator

        if not self.req_cursor and not response_json['data']['channel']['modLogs']['messagesBySender']['edges']:
            return 3  # user does not have messages on channel

        for message in response_json['data']['channel']['modLogs']['messagesBySender']['edges']:
            if not message['node']:
                self.req_messages_list.append({
                    'cursor': message['cursor'],
                    'type': 1  # no node, automod
                })
                continue

            if 'action' in message['node'].keys():
                self.req_messages_list.append({
                    'text': message['node']['action'],
                    'cursor': message['cursor'],
                    'type': 2  # some action
                })
                continue

            if 'category' in message['node'].keys():
                self.req_messages_list.append({
                    'text': message['node']['category'],
                    'cursor': message['cursor'],
                    'type': 3  # some category
                })
                continue

            message_time = message['node']['sentAt']
            message_time = message_time[0:message_time.rfind('.')].replace('T', ' ')
            message_text = message['node']['content']['text']
            message_user = message['node']['sender']['displayName']
            message_cursor = message['cursor']
            self.req_messages_list.append({
                'time': message_time,
                'user': message_user,
                'text': message_text,
                'cursor': message_cursor,
                'type': 0  # user message
            })
            self.messages_num += 1

        return 0

    def get_user_id(self, user_name):
        data_json = GQLOperations.ReportMenuItem.copy()
        data_json['variables'] = {'channelLogin': user_name}
        response = self.session.post(GQLOperations.url, json=data_json)

        if response.status_code != 200:
            return 1, None
        response_json = response.json()
        if 'data' in response_json and 'user' in response_json['data'] and response_json['data']['user'] is not None and response_json['data']['user']['id'] is not None:
            user_id = response_json['data']['user']['id']
            return 0, user_id
        return 2, None  # user not exist

    def set_data_path(self):
        data_path = os.path.join(os.getcwd(), 'data')
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        self.data_messages_path = os.path.join(data_path, f'chat {self.channel_name} user {self.user_name}.txt')
        self.data_messages_extra_nodes_path = os.path.join(data_path, 'messages extra nodes.txt')
