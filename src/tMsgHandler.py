from tMsgText import tMsgText
from configHandler import configHandler
from tNewTextMsg import tNewTextMsg
from tNewLeftMember import tNewLeftMember
from uData import uData
from tMsgSender import tMsgSender

class messageHandler:
	def __init__(self, token, configHandler, uData, tMsgSender):
		self.token = token
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender

	def handleMessage(self, message):
		# if the chat the message was sent from is active, process message
		if self.configHandler.getCustomGroupConfig(message['message']['chat']['id'])['active']:
			if 'new_chat_members' in message['message']:
				newMessage = message_new_chat_members(message['message'])
			elif 'left_chat_member' in message['message']:
				newMessage = tNewLeftMember(message['message'], self.configHandler, self.uData, self.tMsgSender)
			elif 'forward_from' in message['message']:
				newMessage = message_new_forwarded(message['message'])
			elif 'text' in message['message']:
				newMessage = tNewTextMsg(message['message'], self.configHandler, self.uData)
			elif ('contact' in message['message']) or ('location' in message['message']):
				newMessage = message_new_locationOrContact(message['message'])
		# still allow commands to be processed, even when inactive in chat
		if 'entities' in message['message']:
			for entity in message['message']['entities']:
				if entity['type'] == "bot_command":
					newMessage = message_new_botCommand(message['message'])
					# break the for loop if a bot command is found. It's possible for a user
					# to send multiple bot commands in 1 message; only treat the first one
					# as a bot command, treat any extra commands as text instead
					break