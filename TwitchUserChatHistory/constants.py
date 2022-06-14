CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'


class GQLOperations:
    url = 'https://gql.twitch.tv/gql'

    # get user id from user name
    ReportMenuItem = {
        'operationName': 'ReportMenuItem',
        # 'variables': {
        #     "channelLogin": None
        # },
        'extensions': {
            'persistedQuery': {
                'version': 1,
                'sha256Hash': '8f3628981255345ca5e5453dfd844efffb01d6413a9931498836e6268692a30c'
            }
        }
    }

    # get user messages
    ViewerCardModLogsMessagesBySender = {
        'operationName': 'ViewerCardModLogsMessagesBySender',
        # 'variables': {
        #     'senderID': None,
        #     'channelLogin': None,
        #     'cursor': None
        # },
        'extensions': {
            'persistedQuery': {
                'version': 1,
                'sha256Hash': '437f209626e6536555a08930f910274528a8dea7e6ccfbef0ce76d6721c5d0e7'
            }
        }
    }
