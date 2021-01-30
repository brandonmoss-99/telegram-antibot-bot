import requests, json, random, sys, getopt, time, os, copy
from urllib import parse

def getHelp():
	print("\nList of options:\n\n" +
		"-(t)oken of bot to control\n" +
		"--help to show this help message\n\n")
	sys.exit(0)

# handles fetching of messages, returning basic message info
class messageFetcher:
	def __init__(self, token, pollTimeout=20):
		self.token = token
		self.pollTimeout = pollTimeout
		self.messages = None
		self.messagesParsed = None

	# get new messages, pass in offset of last message to fetch only new ones
	# and mark to telegram servers it can remove messages older than that
	def fetchMessages(self):
		# get updates via long polling (sends HTTPS request, won't hear anything back from API server)
		# until there is a new update to send back, may hang here for a while
		# define which updates want telegram to send us, ignore every other update type
		updatesToFetch = '["message", "callback_query"]'
		updateRequest = sendRequest(["getUpdates", "offset", msgOffset, "timeout", self.pollTimeout, "allowed_updates", updatesToFetch])
		if updateRequest[0] == True:
			#print(updateRequest[2])
			self.messagesParsed = json.loads(updateRequest[2])
			return True
		else:
			print("timestamp:", int(time.time()), "Failed to fetch new messages!", updateRequest[2])
			return False

	# loop through each parsed message stored in the messageFetcher
	def printAllMessages(self):
		for i in range(0, len(self.messagesParsed['result'])):
			print(self.messagesParsed['result'][i],'\n\n')

	def getMessagesLength(self):
		return len(self.messagesParsed['result'])

	# return all messages stored in class
	def getMessages(self):
		return self.messagesParsed

	# return specific message stored in class by position
	def getMessage(self, pos):
		return self.messagesParsed['result'][pos]

	# print specific message stored in class by position
	def printMessage(self, pos):
		print(self.messagesParsed['result'][pos])

	# return type of specified message stored in class by position
	def getMessageType(self, pos):
		test = list(pos.keys())
		return test[1]


class messageHandler:
	def __init__(self, token):
		self.token = token

	def handleMessage(self, message):
		# if the chat the message was sent from is active, process message
		if config.getCustomGroupConfig(message['message']['chat']['id'])['active']:
			if 'new_chat_members' in message['message']:
				newMessage = message_new_chat_members(message['message'])
			elif 'left_chat_member' in message['message']:
				newMessage = message_new_left_members(message['message'])
			elif 'forward_from' in message['message']:
				newMessage = message_new_forwarded(message['message'])
			elif 'text' in message['message']:
				newMessage = message_new_text(message['message'])
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


class message_new_botCommand:
	def __init__(self, message):
		self.message = message
		self.getInfo()
		# get up-to-date list of admins. The command should only be processed if
		# the person who sent the command is an admin of the chat it was sent from
		getAdminsResponse = sendRequest(["getChatAdministrators", "chat_id", self.chat['id']])
		# only process commands if a list of admins could be fetched
		# don't want just anyone running the commands
		if getAdminsResponse[0] == True:
			# make list of admin IDs from results
			chatAdminIDs = [user['user']['id'] for user in json.loads(getAdminsResponse[2])['result']]
			# if the bot command was sent from a group admin
			if self.isfrom['id'] in chatAdminIDs:
				# check if the command and parameters are valid
				commandStringValid = self.checkBotCommandStringValid()
				commandParamValid = self.checkBotCommandParamValid()
				# if the command and parameters are valid, 
				# make new commandHandler and run the command with the parameter
				# and reply
				if commandStringValid and commandParamValid:
					groupConfig = self.getChatInfo()
					commandHandle = commandHandler()
					commandResponse = commandHandle.runCommandGroupData(self.commandParsed, self.botCommandParam, groupConfig)
					#commandResponse = commandHandle.runCommand(self.commandParsed, self.botCommandParam)
					self.reply(commandResponse)
				elif commandStringValid and not commandParamValid:
					self.reply([False, "Failed, something is wrong with the value after your command", "Command parameter was invalid"])
				else:
					self.reply([False, "Failed, something is wrong with your command and/or value after it", "Command was invalid"])
			else:
				self.reply([False, "You don't have permission to run this command!", "Unauthorised user tried running command"])
		else:
			self.reply([False, "Failed, couldn't acquire the list of admins. For safety, commands can't run until a list of admins can be established!", "Failed to get admin list for chat"])

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
		if self.botCommandLength > len(bot_username)+2:
			self.commandParsed = self.botCommandText[1:(self.botCommandLength - len(bot_username)-1)]
		else:
			self.commandParsed = self.botCommandText[1:]

		# check if the command sent to the bot is one it can work with
		if self.commandParsed in list(botCommandsInfo):
			return True
		else:
			return False

	def checkBotCommandParamValid(self):
		# checking for a positive integer requirement
		if botCommandsInfo[self.commandParsed]['paramType'] == 'posint':
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
		elif botCommandsInfo[self.commandParsed]['paramType'] == 'bool':
			try:
				# get all text in message after 1st bot command
				self.trailingText = self.message['text'][self.botCommandOffset+self.botCommandLength:]
				self.botCommandParam = bool(self.trailingText)
				return True
			except Exception as e:
				return False

		# if command doesn't require any parameter
		elif botCommandsInfo[self.commandParsed]['paramType'] == 'none':
			# ignore whatever parameter was set, probably valid
			self.botCommandParam = None
			return True

	def getChatInfo(self):
		groupConfig = config.getCustomGroupConfig(self.chat['id'])

		# make newConfig a deep copy of the dictionary
		# passed in, so if the group passed in is the 
		# default group, we can leave it unchanged
		newGroupConfig = copy.deepcopy(groupConfig)
		if groupConfig['id'] == '0':
			newGroupConfig['id'] = str(self.chat['id'])
		return newGroupConfig

	def reply(self, commandResponse):
		response = commandResponse[1]
		sendResponse = sendRequest(["sendMessage", "chat_id", self.chat['id'], "text", response])
		# if operation failed, output error
		if commandResponse[0] == False:
			print(commandResponse[1], "-", commandResponse[2], ":", self.message['text'])


class commandHandler:

	def runCommand(self, command, param):
		self.command = command
		self.param = param
		# use the command passed in to choose the function to run
		# return False if a function for that command name isn't found
		commandToRun = getattr(self, self.command, False)
		if commandToRun != False:
			return commandToRun(self.param)
		else:
			return [False, "Couldn't find function", self.command]

	def runCommandGroupData(self, command, param, groupConfig):
		self.command = command
		self.param = param
		self.groupConfig = groupConfig
		# use the command passed in to choose the function to run
		# return False if a function for that command name isn't found
		commandToRun = getattr(self, self.command, False)
		if commandToRun != False:
			return commandToRun(self.param, self.groupConfig)
		else:
			return [False, "Couldn't find function", self.command]

	# set unvalidatedTimeToKick
	def setunvalttk(self, param, groupConfig):
		try:
			#print("old config: ", config.configGroupsData)
			self.groupConfig['unValidatedTimeToKick'] = self.param
			config.setCustomGroupConfig(self.groupConfig)
			#print("\n\nnew config: ", config.configGroupsData)
			return [True, "Successfully set unvalidated time to kick to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set unvalidated time to kick to " + str(param) + " seconds", str(e)]

	# set validatedTimeToKick
	def setvalttk(self, param, groupConfig):
		try:
			self.groupConfig['validatedTimeToKick'] = self.param
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set validated time to kick to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set validated time to kick to " + str(param) + " seconds", str(e)]

	# set timeToRestrict
	def setrestricttime(self, param, groupConfig):
		try:
			self.groupConfig['timeToRestrict'] = self.param
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set button tap restriction time to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set button tap restriction time to " + str(param) + " seconds", str(e)]

	# set timeToDelete
	def setdeletetime(self, param, groupConfig):
		try:
			self.groupConfig['timeToDelete'] = self.param
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set time to delete my messages to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set time to delete my messages to " + str(param) + " seconds", str(e)]

	# set timeToRestrictForwards
	def setfrstmsgrtime(self, param, groupConfig):
		try:
			self.groupConfig['timeToRestrictForwards'] = self.param
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set time to monitor new user's messages for anything prohibited after their first message to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set time to monitor new user's messages for anything prohibited after their first message to " + str(param) + " seconds", str(e)]

	def disable(self, param, groupConfig):
		try:
			self.groupConfig['active'] = False
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully disabled the bot from responding to new events"]
		except Exception as e:
			return [False, "Failed to disable the bot from responding to new events ", str(e)]

	def enable(self, param, groupConfig):
		try:
			self.groupConfig['active'] = True
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully enabled the bot to respond to new events"]
		except Exception as e:
			return [False, "Failed to enable the bot to respond to new events ", str(e)]

	# Use with caution! A lockdown will auto-ban every new user joining until disabled!
	def lockdown(self, param, groupConfig):
		try:
			self.groupConfig['inLockdown'] = True
			config.setCustomGroupConfig(self.groupConfig)
			# if the bot is not responding to new events when a lockdown
			# command is sent, re-enable the bot to respond
			if self.groupConfig['active'] == False:
				enableCommand = self.enable(None, self.groupConfig)
				# if bot was successfully re-enabled, enter lockdown
				if enableCommand[0] == True:
					return [True, "\U0001F6A8 !!! LOCKDOWN ENABLED !!! \U0001F6A8 %0A%0ABot was automatically re-enabled to respond! %0A%0AAll new users will be insta-banned until disabled!"]
				else:
					return [False, "Lockdown failed! Couldn't automatically re-enable the bot! ", str(e)]
			else:
				return [True, "\U0001F6A8 !!! LOCKDOWN ENABLED !!! \U0001F6A8 %0A%0AAll new users will be insta-banned until disabled!"]
		except Exception as e:
			return [False, "Lockdown failed! Admin to manually disable global group permissions! ", str(e)]

	def disablelockdown(self, param, groupConfig):
		try:
			self.groupConfig['inLockdown'] = False
			config.setCustomGroupConfig(self.groupConfig)
			return [True, "Lockdown successfully disabled"]
		except Exception as e:
			return [False, "Lockdown failed to disable! ", str(e)]


class message_new_text:
	def __init__(self, message):
		self.message = message
		self.getInfo()
		# if the message sent is from a new user in the newUsers dictionary,
		# set their hasSentGoodMessage property to True, to mark them to be
		# deleted from the dictionary
		if self.isfrom['id'] + self.chat['id'] in newUsers:
			# add message to newUsers list of messages
			newUsers[self.isfrom['id'] + self.chat['id']]['sentMessages'].append(self.message_id)
			# if user has sent an entity in their 1st text message, delete their message and mark for kicking
			if ('entities' in self.message) and (self.message['entities'][0]['type'] in config.getCustomGroupConfig(self.chat['id'])['bannedEntities']):
				newUsers[self.isfrom['id'] + self.chat['id']]['hasSentBadMessage'] = True
			else:
				newUsers[self.isfrom['id'] + self.chat['id']]['hasSentGoodMessage'] = True
				# if the user hasn't already sent a message, set their first message time to current unix time
				if newUsers[self.isfrom['id'] + self.chat['id']]['timeSentFirstMessage'] == None:
					newUsers[self.isfrom['id'] + self.chat['id']]['timeSentFirstMessage'] = int(time.time())

	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		# include optional message data
		self.isfrom = self.message['from']


class message_new_forwarded:
	def __init__(self, message):
		self.message = message
		self.getInfo()

		# if user has sent forwarded message, check if they're still in newUsers
		# if not sent a message yet, or their first message was sent less than
		# x mins ago, delete their message and mark for kicking
		if self.isfrom['id'] + self.chat['id'] in newUsers:
			if ((newUsers[self.isfrom['id'] + self.chat['id']]['timeSentFirstMessage'] == None) or 
				(int(time.time()) - newUsers[self.isfrom['id'] + self.chat['id']]['timeSentFirstMessage'] <= config.getCustomGroupConfig(self.chat['id'])['timeToRestrictForwards'])):
					# add message to newUsers list of messages
					newUsers[self.isfrom['id'] + self.chat['id']]['sentMessages'].append(self.message_id)
					newUsers[self.isfrom['id'] + self.chat['id']]['hasSentBadMessage'] = True

	def getInfo(self):
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		self.isfrom = self.message['from'] # optional, but only as not sent when msg sent to channel


class message_new_locationOrContact:
	def __init__(self, message):
		self.message = message
		self.getInfo()

		# if user has sent forwarded message, check if they're still in newUsers
		# if not sent a message yet, or their first message was sent less than
		# x mins ago, delete their message and mark for kicking
		if self.isfrom['id'] + self.chat['id'] in newUsers:
			if ((newUsers[self.isfrom['id'] + self.chat['id']]['timeSentFirstMessage'] == None) or 
				(int(time.time()) - newUsers[self.isfrom['id'] + self.chat['id']]['timeSentFirstMessage'] <= config.getCustomGroupConfig(self.chat['id'])['timeToRestrictForwards']) or
				(int(time.time()) - newUsers[self.isfrom['id'] + self.chat['id']]['timeSetTextRestrictions'] <= config.getCustomGroupConfig(self.chat['id'])['validatedTimeToKick'])):
					# add message to newUsers list of messages
					newUsers[self.isfrom['id'] + self.chat['id']]['sentMessages'].append(self.message_id)
					newUsers[self.isfrom['id'] + self.chat['id']]['hasSentBadMessage'] = True

	def getInfo(self):
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		self.isfrom = self.message['from'] # optional, but only as not sent when msg sent to channel


class message_new_chat_members:
	def __init__(self, message):
		self.message = message
		self.getInfo()
		# for each new member in the new_chat_members array
		for member in self.new_chat_members:
			# if group isn't in lockdown mode
			if config.getCustomGroupConfig(self.chat['id'])['inLockdown'] == False:
				if member['id'] != bot_id and member['is_bot'] == False:
					# restrict new user's permissions to be restricted from everything permanently
					newMemberRestrictions = json.dumps({
						"can_send_messages": False, 
						"can_send_media_messages": False, 
						"can_send_polls": False, 
						"can_send_other_messages": False, 
						"can_add_web_page_previews": False, 
						"can_change_info": False, 
						"can_invite_users": False, 
						"can_pin_messages": False
						})
					sendRequest(["restrictChatMember", "chat_id", self.chat_id, "user_id", member['id'], "permissions", newMemberRestrictions, "until_date", self.date])
					# add user to newUser list
					self.addToList(member)
			# if group is in lockdown mode, auto-ban every new user join
			else:
				banRequest = sendRequest(["kickChatMember", "chat_id", self.chat['id'], "user_id", member['id']])
				if banRequest[0] == False:
					# if the ban failed, output request contents
					print("timestamp:", int(time.time()), "Couldn't ban user_id", member['id'], ":", banRequest[2])
				deleteRequest = sendRequest(["deleteMessage", "chat_id", self.chat['id'], "message_id", self.message_id])
				if deleteRequest[0] == False:
					print("timestamp:", int(time.time()), "Couldn't delete message", self.message_id, "from chat", self.chat['id'],":", banRequest[2])


	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		# extract useful optionally included chat data
		self.new_chat_members = self.message['new_chat_members']
		# set the message type
		self.msgType = 'new_chat_members'
		# extract always included chat data
		self.chat_id = self.chat['id']
		self.chat_type = self.chat['type']
		# extract useful optionally included chat data
		if 'title' in self.chat:
			self.chat_title = self.chat['title']

	# add new user to dictionary of new users
	def addToList(self, member):
		newMember_id = member['id']
		newMember_is_bot = member['is_bot']
		newMember_first_name = member['first_name']
		if 'last_name' in self.message['new_chat_members']:
			newMember_last_name = member['last_name']

		newMember_username = self.message['new_chat_members'][0]['username'] if 'username' in self.message['new_chat_members'][0] else None

		# check the id isn't the bot's id, prevent the bot kicking itself
		if newMember_id != bot_id:
			newUsers[newMember_id + self.chat['id']] = {
			'id':newMember_id,
			'username': newMember_username,
			'firstName':newMember_first_name, 
			'timeJoined':self.date, 'passedValidation':False, 
			'timePassedValidation':None, 
			'timeFailedValidation':None, 
			'hasSentGoodMessage':False, 
			'hasSentBadMessage':False,
			'timeExpiredMessageSendThresh':None, 
			'timeSentFirstMessage':None,
			'timeSentBadMessage':None,
			'timeLiftedRestrictions':None,
			'hasSetTextRestrictions':False,
			'timeSetTextRestrictions':None,
			'chatId':self.chat_id, 
			'joinedMessage':self.message_id,
			'sentMessages':[],
			'welcomeMsgid':[]
			}
		# run reply method to send reply to user
		self.reply(member)

	def reply(self, member):
		# create verify part of prompt
		verifyPrompt = json.dumps({
			"inline_keyboard":[[{"text": "I'm not a robot!", "callback_data": str(member['id'])+str(self.chat['id'])+"Success"}]]})
		# create welcome text part of prompt
		if newUsers[member['id'] + self.chat['id']]['username'] != None:
			welcomeMsg = "Hiya, @" + newUsers[member['id'] + self.chat['id']]['username'] + "%0A%0ATo proceed, please tap the %27I%27m not a robot%21%27 button, within the next%20" + str(int(config.getCustomGroupConfig(self.chat['id'])['unValidatedTimeToKick']/60)) + "%20minutes!%0A%0AOnce done, you%27ll have around%20" + str(config.getCustomGroupConfig(self.chat['id'])['timeToRestrict']) + "%20seconds of full restrictions, then%20" + str(int(config.getCustomGroupConfig(self.chat['id'])['validatedTimeToKick']/60)) + "%20minutes to send a message%20%3A%29"
			welcome = sendRequest(["sendMessage", "chat_id", self.chat_id, "text", welcomeMsg, "entities", "[{'type':'mention', 'offset':6, 'length':" + str(len(member['username'])) + "}]" ,"reply_markup", verifyPrompt])
		else:
			welcomeMsg = "Hiya, " + newUsers[member['id'] + self.chat['id']]['first_name'] + "%0A%0ATo proceed, please tap the %27I%27m not a robot%21%27 button, within the next%20" + str(int(config.getCustomGroupConfig(self.chat['id'])['unValidatedTimeToKick']/60)) + "%20minutes!%0A%0AOnce done, you%27ll have around%20" + str(config.getCustomGroupConfig(self.chat['id'])['timeToRestrict']) + "%20seconds of full restrictions, then%20" + str(int(config.getCustomGroupConfig(self.chat['id'])['validatedTimeToKick']/60)) + "%20minutes to send a message%20%3A%29"
			# send welcomeverify prompt to user
			welcome = sendRequest(["sendMessage", "chat_id", self.chat_id, "text", welcomeMsg, "reply_markup", verifyPrompt])
		if welcome[0] == True:
			# add message id of the welcome message, to know what message
			# to modify/delete later on
			#newUsers[member['id'] + self.chat['id']]['welcomeMsgid'] = json.loads(welcome[2])['result']['message_id']
			newUsers[member['id'] + self.chat['id']]['welcomeMsgid'].append(json.loads(welcome[2])['result']['message_id'])


class message_new_left_members:
	def __init__(self, message):
		self.message = message
		self.getInfo()
		# if lockdown is enabled, try deleting the
		# left message to keep the chat clean
		if config.getCustomGroupConfig(self.chat['id'])['inLockdown'] == True:
			deleteRequest = sendRequest(["deleteMessage", "chat_id", self.chat['id'], "message_id", self.message_id])
			if deleteRequest[0] == False:
				print("timestamp:", int(time.time()), "Couldn't delete message", self.message_id, "from chat", self.chat['id'],":", banRequest[2])



	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']


class callback_queryHandler:
	def __init__(self, token):
		self.token = token

	def handleCallbackQuery(self, message):
		newCallbackQuery = message_new_callback_query(message['callback_query'])


class message_new_callback_query:
	def __init__(self, message):
		self.callbackQuery = message
		self.getInfo()
		self.processQuery()

	def getInfo(self):
		self.query_id = self.callbackQuery['id']
		self.query_from = self.callbackQuery['from']
		self.query_chat_instance = self.callbackQuery['chat_instance']
		self.query_message = self.callbackQuery['message']

		if 'data' in self.callbackQuery:
			self.query_data = self.callbackQuery['data']

	def processQuery(self):
		# if the person who joined is the one to push the button, 
		# and not somebody else who can also see it
		if str(self.query_from['id']) + str(self.query_message['chat']['id']) + 'Success' == self.query_data:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])
			try:
				# update newUsers to mark user as having passed validation, and
				# fill in the time of validation for permission managment/validatedTimeToKick
				newUsers[self.query_from['id'] + self.query_message['chat']['id']]['passedValidation'] = True
				newUsers[self.query_from['id'] + self.query_message['chat']['id']]['timePassedValidation'] = int(time.time())

				# send new message. If that succeeds, add it to current messages 
				# shown in chat, then try and delete the last message sent
				if newUsers[self.query_from['id'] + self.query_message['chat']['id']]['username'] != None:
					validatedMessage = "Yay, @" + newUsers[self.query_from['id'] + self.query_message['chat']['id']]['username'] + "%20 has passed validation%21%0A%0ATo ensure you aren%27t just a clever bot that can press buttons, you%27ll be restricted for around another%20" + str(config.getCustomGroupConfig(self.query_message['chat']['id'])['timeToRestrict']) + "%20seconds!"
					newTextMessageRequest = sendRequest(["sendMessage", "chat_id", self.query_message['chat']['id'], "text", validatedMessage, "entities", "[{'type':'mention', 'offset':5, 'length':" + str(len(newUsers[self.query_from['id'] + self.query_message['chat']['id']]['username'])) + "}]"])
				else:
					validatedMessage = "Yay, " + self.query_from['first_name'] + "%20 has passed validation%21%0A%0ATo ensure you aren%27t just a clever bot that can press buttons, you%27ll be restricted for around another%20" + str(config.getCustomGroupConfig(self.query_message['chat']['id'])['timeToRestrict']) + "%20seconds!"
					newTextMessageRequest = sendRequest(["sendMessage", "chat_id", self.query_message['chat']['id'], "text", validatedMessage])

				if newTextMessageRequest[0] == True:
					newUsers[self.query_from['id'] + self.query_message['chat']['id']]['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
					deleteRequest = sendRequest(["deleteMessage", "chat_id", self.query_message['chat']['id'], "message_id", newUsers[self.query_from['id'] + self.query_message['chat']['id']]['welcomeMsgid'].pop(len(newUsers[self.query_from['id'] + self.query_message['chat']['id']]['welcomeMsgid'])-2)])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[self.query_from['id'] + self.query_message['chat']['id']]['welcomeMsgid'][len(newUsers[self.query_from['id'] + self.query_message['chat']['id']]['welcomeMsgid'])-2], ":", deleteRequest[2])


			except Exception as e:
				print("timestamp:", int(time.time()), "Couldn't edit user", self.query_from['id'], "dictionary entry: ", str(e))
		# if the IDs don't match up
		else:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerFail'])


class config:
	def __init__(self, configFilePath):
		self.configFilePath = configFilePath
		self.configDefaultGroupData = None
		self.configGroupsData = None
		self.configData = None

	def loadConfig(self):
		with open(self.configFilePath, 'r') as configFile:
			try:
				self.configData = json.load(configFile)
				return [True, "Config loaded successfully"]
			except Exception as e:
				return [False, "Error parsing the config file: " + str(e)]

	def loadBotConfig(self):
		varsToLoad = ["msgOffset", "pollTimeout", "whiteListFile"]
		if 'config' in self.configData:
			try:
				for var in varsToLoad:
					globals()[var] = self.configData['config']['bot'][var]
				return [True, "Bot config loaded successfully"]
			except Exception as e:
				return [False, "Error loading bot variables from config file: " + str(e)]
		else:
			return [False, "Error, config section doesn't exist in the file!"]

	def loadDefaultGroupConfig(self):
		if 'config' in self.configData and 'groups' in self.configData['config']:
			try:
				self.configDefaultGroupData = self.configData['config']['groups']['default']
				return [True, "Default group config loaded successfully"]
			except Exception as e:
				return [False, "Error loading default group config from file: " + str(e)]
		else:
			return [False, "Error, config/group/default section doesn't exist in the file!"]

	def loadGroupConfigs(self):
		if 'config' in self.configData and 'groups' in self.configData['config']:
			try:
				self.configGroupsData = self.configData['config']['groups']['custom']
				return [True, "Default group config loaded successfully"]
			except Exception as e:
				return [False, "Error loading custom group configs from file: " + str(e)]
		else:
			return [False, "Error, config/group/custom section doesn't exist in the file!"]

	def getCustomGroupConfig(self, groupId):
		# if the groupId requested exists in config data
		# return that group data, otherwise return the
		# default group config data
		if str(groupId) in self.configGroupsData:
			return self.configGroupsData[str(groupId)]
		else:
			return self.configDefaultGroupData

	def setCustomGroupConfig(self, groupConfigToChange):
		# if the group to change config already exists,
		# replace it with new groupConfig
		#if groupConfigToChange['id'] in self.configGroupsData:
		self.configGroupsData[groupConfigToChange['id']] = groupConfigToChange
		self.writeConfig()

	def writeConfig(self):
		with open('config.txt', 'w') as configFile:
			try:
				json.dump(self.configData, configFile, indent=4)
			except Exception as e:
				print("Failed to write file!")


def handleWrongChat():
	print("timestamp:", int(time.time()), "New msg from a non-whitelisted group, ID: ", msg['message']['chat']['id'])
	sendRequest(["sendMessage", "chat_id", msg['message']['chat']['id'], "text", "Hi there%21%0A%0AI appreciate the add to your group, however right now I only work on specific groups%21"])
	sendRequest(["leaveChat", "chat_id", msg['message']['chat']['id']])


def processNewUserList():
	currentUnixTime = int(time.time())
	# iterate over newUsers dictionary, checking if anyone needs kicking
	toDelete = []
	for key in newUsers:
		# get group info for the user, saves making lots of getConfig requests
		groupInfo = config.getCustomGroupConfig(newUsers[key]['chatId'])

		# if the user hasn't passed validation, and
		# has been in chat longer than the kick duration, 
		# and hasn't already got a failed verfication time,
		# kick them, and add the time they were kicked to
		# their newUsers entry (to know when to delete the msgs)
		if ((newUsers[key]['passedValidation'] == False) and 
			(currentUnixTime - newUsers[key]['timeJoined'] > groupInfo['unValidatedTimeToKick']) and 
			(newUsers[key]['timeFailedValidation'] == None)):
				newUsers[key]['timeFailedValidation'] = currentUnixTime

				# send new message. If that succeeds, add it to current messages 
				# shown in chat, then try and delete the last message sent
				newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", newUsers[key]['firstName'] + "%20didn%27t press the button in time, and was kicked"])
				if newTextMessageRequest[0] == True:
					newUsers[key]['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'].pop(len(newUsers[key]['welcomeMsgid'])-2)])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'][len(newUsers[key]['welcomeMsgid'])-2], ":", deleteRequest[2])
				# kick user
				kickRequest = sendRequest(["unbanChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id']])
				if kickRequest[0] == False:
					# if the kick didn't work, try banning instead
					print("timestamp:", int(time.time()), "Failed to kick, attempting to ban...")
					banRequest = sendRequest(["kickChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id']])
					if banRequest[0] == False:
						# if the ban failed, output request contents
						print("timestamp:", int(time.time()), "Couldn't ban user_id", newUsers[key]['id'], ":", banRequest[2])


		# if the user hasn't passed validation, and
		# has been in chat longer than the kick duration,
		# and has a failed verification time that is longer
		# than the timeToDelete value, OR
		# if the user has passed validation, but hasn't sent any messages
		# for longer than the validatedTimeToKick time, and has an expired
		# message time longer than the timeToDelete value, OR
		# user has passed validation, sent a bad message and has a timeSentBadMsg
		# longer than the timeToDelete value
		# delete the messages
		# and mark them for deletion from the newUsers dictionary
		elif (((newUsers[key]['passedValidation'] == False) and 
			(currentUnixTime - newUsers[key]['timeJoined'] > groupInfo['unValidatedTimeToKick']) and 
			(currentUnixTime - newUsers[key]['timeFailedValidation'] > groupInfo['timeToDelete'])) or
			((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == False) and 
			(currentUnixTime - newUsers[key]['timeJoined'] >= groupInfo['validatedTimeToKick']) and 
			(newUsers[key]['timeExpiredMessageSendThresh'] != None) and
			(currentUnixTime - newUsers[key]['timeExpiredMessageSendThresh'] > groupInfo['timeToDelete'])) or
			((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentBadMessage'] == True) and 
			(newUsers[key]['timeSentBadMessage'] != None) and
			(currentUnixTime - newUsers[key]['timeSentBadMessage'] > groupInfo['timeToDelete']))):
				# cleanup messages here
				for msg in range(len(newUsers[key]['welcomeMsgid'])):
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'][msg-1]])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'][msg-1], ":", deleteRequest[2])
				deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['joinedMessage']])
				if deleteRequest[0] == False:
					print("timestamp:", int(time.time()), "Couldn't delete message", newUsers[key]['joinedMessage'], ":", deleteRequest[2])
				# mark newUser for deletion from dictionary
				toDelete.append(key)


		# if the user has passed validation, but hasn't sent any messages
		# for longer than the validatedTimeToKick time, assume they are
		# a bot (or not interested), kick them and add the time they were
		# kicked to their newUsers entry (to know when to delete the msgs)
		elif ((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == False) and 
			(newUsers[key]['hasSentBadMessage'] == False) and
			(currentUnixTime - newUsers[key]['timeJoined'] > groupInfo['validatedTimeToKick']) and 
			(newUsers[key]['timeExpiredMessageSendThresh'] == None)):
				newUsers[key]['timeExpiredMessageSendThresh'] = currentUnixTime

				# send new message. If that succeeds, add it to current messages 
				# shown in chat, then try and delete the last message sent
				newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", newUsers[key]['firstName'] + "%20didn%27t say anything in the time threshold, and was kicked"])
				if newTextMessageRequest[0] == True:
					newUsers[key]['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'].pop(len(newUsers[key]['welcomeMsgid'])-2)])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'][len(newUsers[key]['welcomeMsgid'])-2], ":", deleteRequest[2])
				
				# kick user
				kickRequest = sendRequest(["unbanChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id']])
				if kickRequest[0] == False:
					# if the kick didn't work, try banning instead
					print("timestamp:", int(time.time()), "Failed to kick, attempting to ban...")
					banRequest = sendRequest(["kickChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id']])
					if banRequest[0] == False:
						# if the ban failed, output request contents
						print("timestamp:", int(time.time()), "Couldn't ban user_id", newUsers[key]['id'], ":", banRequest[2])


		# if the user has passed validation, but hasn't sent any messages,
		# is within the validatedTimeToKick, and passed the restriction
		# time, give them text only privilages for their 1st message send
		elif ((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == False) and 
			(newUsers[key]['hasSentBadMessage'] == False) and
			(currentUnixTime - newUsers[key]['timeJoined'] < groupInfo['validatedTimeToKick'])):
				if ((currentUnixTime - newUsers[key]['timePassedValidation'] >= groupInfo['timeToRestrict']) and 
					(newUsers[key]['hasSetTextRestrictions'] == False)):
					newMemberRestrictions = json.dumps({
						"can_send_messages": True, 
						"can_send_media_messages": False, 
						"can_send_polls": False, 
						"can_send_other_messages": False, 
						"can_add_web_page_previews": False, 
						"can_change_info": False, 
						"can_invite_users": False, 
						"can_pin_messages": False
						})

					# send new message. If that succeeds, add it to current messages 
					# shown in chat, then try and delete the last message sent
					if newUsers[key]['username'] != None:
						newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", "@" + newUsers[key]['username'] + ",%20your restriction time is over!%0A%0APlease send a plain text message like a hello within the next%20" + str(int(groupInfo['validatedTimeToKick']/60)) + "%20minutes, to lift your other restrictions%0A%0A%28I%27d let you send a sticker if the bot API allowed just text and stickers%29%20%3A%29%0A%0ANote%3A Sending any of the following may get you banned - URL, Email, Phone Number, Forwarded Message, Contact, Location or a Bot Command", "entities", "[{'type':'mention', 'offset':0, 'length':" + str(len(newUsers[key]['username'])) + "}]"])
					else:
						newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", newUsers[key]['firstName'] + ",%20your restriction time is over!%0A%0APlease send a plain text message like a hello within the next%20" + str(int(groupInfo['validatedTimeToKick']/60)) + "%20minutes, to lift your other restrictions%0A%0A%28I%27d let you send a sticker if the bot API allowed just text and stickers%29%20%3A%29%0A%0ANote%3A Sending any of the following may get you banned - URL, Email, Phone Number, Forwarded Message, Contact, Location or a Bot Command"])
					if newTextMessageRequest[0] == True:
						newUsers[key]['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
						deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'].pop(len(newUsers[key]['welcomeMsgid'])-2)])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'][len(newUsers[key]['welcomeMsgid'])-2], ":", deleteRequest[2])
					
					permEditRequest = sendRequest(["restrictChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id'], "permissions", newMemberRestrictions, "until_date", currentUnixTime])
					if permEditRequest[0] == True:
						newUsers[key]['hasSetTextRestrictions'] = True
						newUsers[key]['timeSetTextRestrictions'] = currentUnixTime
					elif permEditRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to change permissions for", newUsers[key]['id'], ":", permEditRequest[2])



		# if the user has passed validation, but has sent a prohibited message,
		# ban them from group & add time kicked to their newUsers entry 
		# (to know when to delete the msgs)
		elif ((newUsers[key]['passedValidation'] == True) and
			(newUsers[key]['hasSentBadMessage'] == True) and
			(newUsers[key]['timeSentBadMessage'] == None)):
				newUsers[key]['timeSentBadMessage'] = currentUnixTime

				# delete all messages the user has sent, since joining the chat
				for userMessage in newUsers[key]['sentMessages']:
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", userMessage])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Couldn't delete message ID", userMessage, ":", deleteRequest[2])

				# send new message. If that succeeds, add it to current messages 
				# shown in chat, then try and delete the last message sent
				newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", newUsers[key]['firstName'] + "%20sent something not permitted for their first message, and was banned"])
				if newTextMessageRequest[0] == True:
					newUsers[key]['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'].pop(len(newUsers[key]['welcomeMsgid'])-2)])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'][len(newUsers[key]['welcomeMsgid'])-2], ":", deleteRequest[2])
				
				banRequest = sendRequest(["kickChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id']])
				if banRequest[0] == False:
					# if the ban failed, output request contents
					print("timestamp:", int(time.time()), "Couldn't ban user_id", newUsers[key]['id'], ":", banRequest[2])



		# if the user has passed validation, and has sent a message,
		# give them all normal privilages permanently
		elif ((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == True) and
			newUsers[key]['timeLiftedRestrictions'] == None):
				newUsers[key]['timeLiftedRestrictions'] = currentUnixTime
				
				# send new message. If that succeeds, add it to current messages 
				# shown in chat, then try and delete the last message sent
				if newUsers[key]['username'] != None:
					newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", "Welcome @" + newUsers[key]['username'] + "%21 %0A%0APlease refrain from sending any forwarded messages, locations or contacts here for another " + str(int((groupInfo['timeToRestrictForwards']/60)+1)) + " minutes%21 %28When this message is deleted%29", "entities", "[{'type':'mention', 'offset':8, 'length':" + str(len(newUsers[key]['username'])) + "}]"])
				else:
					newTextMessageRequest = sendRequest(["sendMessage", "chat_id", newUsers[key]['chatId'], "text", "Welcome " + newUsers[key]['firstName'] + "%21 %0A%0APlease refrain from sending any forwarded messages, locations or contacts here for another " + str(int((groupInfo['timeToRestrictForwards']/60)+1)) + " minutes%21 %28When this message is deleted%29"])
				if newTextMessageRequest[0] == True:
					newUsers[key]['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'].pop(len(newUsers[key]['welcomeMsgid'])-2)])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'][len(newUsers[key]['welcomeMsgid'])-2], ":", deleteRequest[2])

				# give permanent privilages
				newMemberRestrictions = json.dumps({
					"can_send_messages": True, 
					"can_send_media_messages": True, 
					"can_send_polls": True, 
					"can_send_other_messages": True, 
					"can_add_web_page_previews": True, 
					"can_change_info": False, 
					"can_invite_users": True, 
					"can_pin_messages": False
					})

				permEditRequest = sendRequest(["restrictChatMember", "chat_id", newUsers[key]['chatId'], "user_id", newUsers[key]['id'], "permissions", newMemberRestrictions, "until_date", currentUnixTime])
				if permEditRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to change permissions for", newUsers[key]['id'], ":", permEditRequest[2])


		# if the user has passed validation, sent a message, 
		# has already had their restrictions lifted and sent
		# their 1st msg longer than timeToRestrictForwards seconds
		# ago (+ 1 minute for safety like the message),
		# delete the welcome messages and mark them for deletion
		# from newUsers dictionary
		elif ((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == True) and
			(newUsers[key]['timeLiftedRestrictions'] != None) and
			(currentUnixTime - newUsers[key]['timeSentFirstMessage'] > groupInfo['timeToRestrictForwards'] + 60)):

				# delete welcome message. Don't delete join message, want to see in past when a genuine user joins the chat
				for msg in range(len(newUsers[key]['welcomeMsgid'])):
					deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'][msg-1]])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'], ":", deleteRequest[2])
				
				# mark newUser for deletion from dictionary
				toDelete.append(key)


	# delete kicked users from the newUsers table
	for user in toDelete:
		try:
			del newUsers[user]
		except Exception as e:
			print("timestamp:", int(time.time()), "Failed to remove user", user, ":", str(e))


def sendRequest(msgParams):
	# if there's multiple parameters, have to append them correctly
	if len(msgParams) > 0:
		requestString = "https://api.telegram.org/bot"+str(token)+"/"+str(msgParams[0])+"?"
		# skip the 0th item, already appended it to the requestString
		for i in range(1, len(msgParams)-1, 2):
			requestString = requestString + str(msgParams[i]) + "=" + str(msgParams[i+1]) + "&"
		requestString = requestString + str(msgParams[-1])
	else:
		requestString = "https://api.telegram.org/bot"+str(token)+"/"+str(msgParams[0])

	try:
		request = requests.get(requestString)
		# return True/False for a status code of 2XX, the status code itself and the response content
		if request.ok:
			return [True, request.status_code, request.content]
		else:
			return [False, request.status_code, request.content]
	except Exception as e:
		return [False, 0, "Error whilst making the request:", requestString, "\nError:",str(e)]


def readIntFileToList(path):
	if os.path.isfile(path):
		try:
			with open(path, "r") as f:
				# read each line in file, stripping any trailing chars ('/n') and casting to int
				lines = [int(line.rstrip()) for line in f]
			return [True, lines]
		except Exception as e:
			print("Error whilst handling", path, ":", str(e))
			return [False, []]
	else:
		return [False, []]


if __name__ == '__main__':
	# initial token value
	token = ""
	argv = sys.argv[1:]

	# try getting supported parameters and args from command line
	try:
		opts, args = getopt.getopt(argv, "t:",
			["token=", "help"])
	except:
		print("Error parsing options")
		getHelp()

	for opt, arg in opts:
		if opt in ['-t', '--token']:
			try:
				# connect to Telegram API with their getMe test method for checking API works
				testResponse = requests.get("https://api.telegram.org/bot%s/getMe" % (str(arg)))
				# set the token to be used if we get a 2xx response code back
				if testResponse.ok:
					token = str(arg)
				else:
					print("Error validating your token!")
					getHelp()
			except:
				print("Error trying to validate your token!")
				getHelp()
		if opt in ['--help']:
			getHelp()
	print("--------------------------------------\nProgram started at UNIX time:", int(time.time()), "\n")

	# load configurations
	config = config('config.txt')
	print(config.loadConfig()[1])
	print(config.loadBotConfig()[1])
	defaultConfLoad = config.loadDefaultGroupConfig()
	customConfLoad = config.loadGroupConfigs()
	# if the default group config or custom group config can't be found
	# stop program, needs to be fixed
	if not defaultConfLoad[0] or not customConfLoad[0]:
		print("Default config: ", defaultConfLoad[1], "Custom group config: ", customConfLoad[1])
		sys.exit(0)


	# dictionary of new users who need to be kept track of until
	# new user requirements are satisfied
	newUsers = {}

	botCommandsInfo = {
		"enable":{
			"name":"enable",
			"description":"Enable the bot, respond to new events",
			"paramType":"none"
		},
		"disable":{
			"name":"disable",
			"description":"Disable the bot, ignore new events",
			"paramType":"none"
		},
		"setunvalttk":{
			"name":"setunvalttk",
			"description":"Set how many seconds user has to press button before being kicked",
			"paramType":"posint"
		},
		"setvalttk":{
			"name":"setvalttk",
			"description":"Set how many seconds user has to send something after being validated",
			"paramType":"posint"
		},
		"setrestricttime":{
			"name":"setrestricttime",
			"description":"Set how many seconds a user is restricted for after being validated",
			"paramType":"posint"
		},
		"setdeletetime":{
			"name":"setdeletetime",
			"description":"Set how many seconds until bot messages are automatically deleted (after task is done)",
			"paramType":"posint"
		},
		"setfrstmsgrtime":{
			"name":"setfrstmsgrtime",
			"description":"Set how many seconds to monitor a new users messages for something prohibited after sending their 1st message",
			"paramType":"posint"
		},
		"lockdown":{
			"name":"lockdown",
			"description":"CAUTION: Will auto-ban every new user join until disabled",
			"paramType":"none"
		},
		"disablelockdown":{
			"name":"disablelockdown",
			"description":"Disable lockdown mode",
			"paramType":"none"
		}
	}

	# turn botCommands into the type of list telegram requires for setMyCommands method
	botCommandsAsList = list(botCommandsInfo.items())
	botCommandsForTelegram = '['
	botCommandsForTelegram = botCommandsForTelegram + '{"command":"' + botCommandsAsList[0][1]['name'] + '", "description":"' + botCommandsAsList[0][1]['description'] + '"}'
	for command in botCommandsAsList:
		botCommandsForTelegram = botCommandsForTelegram + ', {"command":"' + command[1]['name'] + '", "description":"' + command[1]['description'] + '"}'
	botCommandsForTelegram = botCommandsForTelegram + ']'
	commandRequest = sendRequest(["setMyCommands", "commands", botCommandsForTelegram])

	# Chat IDs to work with. Don't want just anyone adding the bot and sucking up the host's resources!
	whiteListRead = readIntFileToList(whiteListFile)
	if whiteListRead[0] == True:
		usingWhitelistRestrictions = True
		whitelistedChatIDs = whiteListRead[1]
		print("Using whitelist restrictions")
	else:
		usingWhitelistRestrictions = False
		print("Whitelist file not found/processing failed, disabling whitelist restrictions")

	botInfo = json.loads(sendRequest(["getMe"])[2])['result']
	bot_id = botInfo['id']
	bot_username = botInfo['username']
	messageFetcher = messageFetcher(token, pollTimeout)
	messageHandler = messageHandler(token)
	callback_queryHandler = callback_queryHandler(token)

	# loop, run until program is quit
	while True:
		# fetch all the new messages from Telegram servers
		if messageFetcher.fetchMessages() == True:
			# for each message in the list of new messages
			for i in range(messageFetcher.getMessagesLength()):
				# get the message
				msg = messageFetcher.getMessage(i)
				# check the message type and hand message off to handler
				if 'message' in msg:
					# if we're using a whitelist to restrict chats we deal with
					if usingWhitelistRestrictions == True:
						# if a message comes from a whitelisted chat, deal with it, otherwise
						# send a message and remove the bot from the chat the message came from
						if msg['message']['chat']['id'] in whitelistedChatIDs:
							messageHandler.handleMessage(msg)
						else:
							handleWrongChat()
					# if we're not using a whitelist to restrict chats, 
					# handle message without checking chat origin
					else:
						messageHandler.handleMessage(msg)

				# callback query is from tapping a button sent with message
				elif 'callback_query' in msg:
					callback_queryHandler.handleCallbackQuery(msg)

				# update the message offset, so it is 'forgotten' by telegram servers
				# and not returned again on next fetch for new messages, as we've
				# (hopefully) dealt with the message now
				msgOffset = msg['update_id'] + 1

			processNewUserList()
		else:
			# failed to fetch new messages, wait for random number of seconds then try again
			# (may reduce strain on telegram servers when requests are randomly distributed if
			# they go down, instead of happening at fixed rate along with many other bots etc)
			time.sleep(random.randint(20, 60))

