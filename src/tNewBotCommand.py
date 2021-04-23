import time, json, copy
from tMsgSender import tMsgSender
from configHandler import configHandler
from uData import uData
from tBotCommandInfo import tBotCommandInfo
from tCommandHandler import tCommandHandler

class tNewBotCommand:
	def __init__(self, message, configHandler, uData, tMsgSender, bot_username, tBotCommandInfo, tCommandHandler):
		self.message = message
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender
		self.tBotCommandInfo = tBotCommandInfo
		self.tCommandHandler = tCommandHandler
		self.bot_username = bot_username
		self.getInfo()

		# parse the command and check if it's valid to the list of commands
		commandStringValid = self.checkBotCommandStringValid()
		if commandStringValid:
			# get up-to-date list of admins. The command should only be processed if
			# the person who sent the command is an admin of the chat it was sent from
			getAdminsResponse = self.tMsgSender.sendRequest(["getChatAdministrators", "chat_id", self.chat['id']])
			# only process commands if a list of admins could be fetched
			# don't want just anyone running the commands
			if getAdminsResponse[0] == True:
				# make list of admin IDs from results
				chatAdminIDs = [user['user']['id'] for user in json.loads(getAdminsResponse[2])['result']]
				# if the bot command was sent from a group admin
				if self.isfrom['id'] in chatAdminIDs:
					# check if the command parameters are valid
					commandParamValid = self.checkBotCommandParamValid()
					# if the command parameters are valid, 
					# make new commandHandler and run the command with the parameter
					# and reply
					if commandParamValid:
						groupConfig = self.getChatInfo()
						commandResponse = self.tCommandHandler.runCommandGroupData(self.commandParsed, self.botCommandParam, groupConfig)
						self.reply(commandResponse)
					else:
						self.reply([False, "Failed, something is wrong with the value after your command", "Command parameter was invalid"])
				else:
					self.reply([False, "You don't have permission to run this command!", "Unauthorised user tried running command"])
			else:
				self.reply([False, "Failed, couldn't acquire the list of admins. For safety, commands can't run until a list of admins is successfully fetched!", "Failed to get admin list for chat"])

	def getInfo(self):
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		# include optional message data
		self.isfrom = self.message['from']
		self.entities = self.message['entities']

		for entity in self.entities:
			if entity['type'] == "bot_command":
				self.botCommandOffset = entity['offset']
				self.botCommandLength = entity['length']
				self.botCommandText = self.message['text'][self.botCommandOffset:self.botCommandLength]
				# break the for loop when 1st bot command is found. It's possible for a user
				# to send multiple bot commands in 1 message; only treat the first one
				# as a bot command, treat any extra commands as text instead
				break

	def checkBotCommandStringValid(self):
		# check what format the command is in, either /command@botusername, or /command &
		# get the command text on it's own, stripping the leading / and the bot's username if needed
		if self.botCommandLength > len(self.bot_username)+2:
			self.commandParsed = self.botCommandText[1:(self.botCommandLength - len(self.bot_username)-1)]
		else:
			self.commandParsed = self.botCommandText[1:]

		# check if the command sent to the bot is one it can work with
		return True if self.tBotCommandInfo.inCommandList(self.commandParsed) else False

	def checkBotCommandParamValid(self):
		# checking for a positive integer requirement
		if self.tBotCommandInfo.getCommandData(self.commandParsed, 'paramType') == 'posint':
			try:
				# get all text in message after 1st bot command
				self.trailingText = self.message['text'][self.botCommandOffset+self.botCommandLength:]
				# try to convert the text into an integer to be used
				self.botCommandParam = int(self.trailingText)
				if self.botCommandParam > 0:
					return True
				else:
					return False
			except Exception as e:
				return False

		# checking for a boolean requirement
		elif self.tBotCommandInfo.getCommandData(self.commandParsed, 'paramType') == 'bool':
			try:
				# get all text in message after 1st bot command
				self.trailingText = self.message['text'][self.botCommandOffset+self.botCommandLength:]
				self.botCommandParam = bool(self.trailingText)
				return True
			except Exception as e:
				return False

		# if command doesn't require any parameter
		elif self.tBotCommandInfo.getCommandData(self.commandParsed, 'paramType') == 'none':
			# ignore whatever parameter was set, probably valid
			self.botCommandParam = None
			return True

	def getChatInfo(self):
		groupConfig = self.configHandler.getCustomGroupConfig(self.chat['id'])

		# make newConfig a deep copy of the dictionary
		# passed in, so if the group passed in is the 
		# default group, we can leave it unchanged
		newGroupConfig = copy.deepcopy(groupConfig)
		if groupConfig['id'] == '0':
			newGroupConfig['id'] = str(self.chat['id'])
		return newGroupConfig

	def reply(self, commandResponse):
		response = commandResponse[1]
		sendResponse = self.tMsgSender.sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", response])
		# if operation failed, output error
		if commandResponse[0] == False:
			print(commandResponse[1], "-", commandResponse[2], ":", self.message['text'])