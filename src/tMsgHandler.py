from tNewTextMsg import tNewTextMsg
from configHandler import configHandler
from tNewTextMsg import tNewTextMsg
from tNewLeftMember import tNewLeftMember
from tNewChatMember import tNewChatMember
from uData import uData
from tMsgSender import tMsgSender
from tNewForwardedMsg import tNewForwardedMsg
from tNewLocOrContact import tNewLocOrContact
from tNewBotCommand import tNewBotCommand
from tBotCommandInfo import tBotCommandInfo
from tCommandHandler import tCommandHandler

class tMsgHandler:
	def __init__(self, token, bot_id, bot_username, configHandler, uData, tMsgSender, tBotCommandInfo):
		self.token = token
		self.bot_id = bot_id
		self.bot_username = bot_username
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender
		self.tBotCommandInfo = tBotCommandInfo
		self.tCommandHandler = tCommandHandler(self.configHandler)

	def handleMessage(self, message):
		# if the chat the message was sent from is active, process message
		if self.configHandler.getCustomGroupConfig(message['message']['chat']['id'])['active']:
			if 'new_chat_members' in message['message']:
				newMessage = tNewChatMember(message['message'], self.bot_id, self.configHandler, self.uData, self.tMsgSender)
			elif 'left_chat_member' in message['message']:
				newMessage = tNewLeftMember(message['message'], self.configHandler, self.uData, self.tMsgSender)
			elif 'forward_from' in message['message']:
				newMessage = tNewForwardedMsg(message['message'], self.configHandler, self.uData)
			elif 'text' in message['message']:
				newMessage = tNewTextMsg(message['message'], self.configHandler, self.uData)
			elif ('contact' in message['message']) or ('location' in message['message']):
				newMessage = tNewLocOrContact(message['message'], self.configHandler, self.uData)
		# still allow commands to be processed, even when inactive in chat
		if 'entities' in message['message']:
			for entity in message['message']['entities']:
				if entity['type'] == "bot_command":
					newMessage = tNewBotCommand(message['message'], self.configHandler, self.uData, self.tMsgSender, self.bot_username, self.tBotCommandInfo, self.tCommandHandler)
					# break the for loop if a bot command is found. It's possible for a user
					# to send multiple bot commands in 1 message; only treat the first one
					# as a bot command, treat any extra commands as text instead
					break