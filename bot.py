import requests, json, random, sys, getopt, time, os
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
		if 'new_chat_members' in message['message']:
			newMessage = message_new_chat_members(message['message'])
		elif 'text' in message['message']:
			newMessage = message_new_text(message['message'])


class message_new_text:
	def __init__(self, message):
		self.message = message
		self.getInfo()
		# if the message sent is from a new user in the newUsers dictionary,
		# set their hasSentGoodMessage property to True, to mark them to be
		# deleted from the dictionary
		if self.isfrom['id'] in newUsers:
			# if user has sent an entity in their 1st text message, delete their message and mark for kicking
			if ('entities' in self.message) and (self.message['entities'][0]['type'] in bannedEntities) or ('forward_from' in self.message):
				newUsers[self.isfrom['id']]['hasSentBadMessage'] = True
				deleteRequest = sendRequest(["deleteMessage", "chat_id", self.chat['id'], "message_id", self.message_id])
				if deleteRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to delete message", self.message_id, ":", deleteRequest[2])
			else:
				newUsers[self.isfrom['id']]['hasSentGoodMessage'] = True

	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		# include optional message data
		self.isfrom = self.message['from']


class message_new_chat_members:
	def __init__(self, message):
		self.message = message
		self.getInfo()
		# for each new member in the new_chat_members array
		for member in self.new_chat_members:
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
		if 'username' in self.message['new_chat_members']:
			newMember_username = member['username']

		# check the id isn't the bot's id, prevent the bot kicking itself
		if newMember_id != bot_id:
			newUsers[newMember_id] = {
			'firstName':newMember_first_name, 
			'timeJoined':self.date, 'passedValidation':False, 
			'timePassedValidation':None, 
			'timeFailedValidation':None, 
			'hasSentGoodMessage':False, 
			'hasSentBadMessage':False,
			'timeExpiredMessageSendThresh':None, 
			'timeSentBadMessage':None,
			'hasSetTextRestrictions': False,
			'chatId':self.chat_id, 
			'joinedMessage':self.message_id
			}
		# run reply method to send reply to user
		self.reply(member)

	def reply(self, member):
		# create verify part of prompt
		verifyPrompt = json.dumps({
			"inline_keyboard":[[{"text": "I'm not a robot!", "callback_data": str(member['id'])+"Success"}]]})
		# create welcom text part of prompt
		welcomeMsg = "Hiya,%20" + member['first_name'] + "%0A%0ATo proceed, please tap the %27I%27m not a robot%21%27 button, within the next%20" + str(int(unValidatedTimeToKick/60)) + "%20minutes!%0A%0AOnce done, you%27ll have around%20" + str(timeToRestrict) + "%20seconds of full restrictions, then%20" + str(int(validatedTimeToKick/60)) + "%20minutes to send a message%20%3A%29"
		# send welcomeverify prompt to user
		welcome = sendRequest(["sendMessage", "chat_id", self.chat_id, "text", welcomeMsg, "reply_markup", verifyPrompt])
		if welcome[0] == True:
			# add message id of the welcome message, to know what message
			# to modify/delete later on
			newUsers[member['id']]['welcomeMsgid'] = json.loads(welcome[2])['result']['message_id']


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
		if str(self.query_from['id']) + 'Success' == self.query_data:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])
			try:
				# update newUsers to mark user as having passed validation, and
				# fill in the time of validation for permission managment/validatedTimeToKick
				newUsers[self.query_from['id']]['passedValidation'] = True
				newUsers[self.query_from['id']]['timePassedValidation'] = int(time.time())
				# edit message contents
				validatedMessage = "Yay,%20" + self.query_from['first_name'] + "%20 has passed validation%21%0A%0ATo ensure you aren%27t just a clever bot that can press buttons, you%27ll be restricted for around another%20" + str(timeToRestrict) + "%20seconds!"
				sendRequest(["editMessageText", "chat_id", self.query_message['chat']['id'], "message_id", self.query_message['message_id'], "text", validatedMessage])
			except Exception as e:
				print("timestamp:", int(time.time()), "Couldn't edit user", self.query_from['id'], "dictionary entry: ", str(e))
		# if the IDs don't match up
		else:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerFail'])


def handleWrongChat():
	print("timestamp:", int(time.time()), "New msg from a non-whitelisted group, ID: ", msg['message']['chat']['id'])
	sendRequest(["sendMessage", "chat_id", msg['message']['chat']['id'], "text", "Hi there%21%0A%0AI appreciate the add to your group, however right now I only work on specific groups%21"])
	sendRequest(["leaveChat", "chat_id", msg['message']['chat']['id']])


def processNewUserList():
	currentUnixTime = int(time.time())
	# iterate over newUsers dictionary, checking if anyone needs kicking
	toDelete = []
	for key in newUsers:
		# if the user hasn't passed validation, and
		# has been in chat longer than the kick duration, 
		# and hasn't already got a failed verfication time,
		# kick them, and add the time they were kicked to
		# their newUsers entry (to know when to delete the msgs)
		if ((newUsers[key]['passedValidation'] == False) and 
			(currentUnixTime - newUsers[key]['timeJoined'] > unValidatedTimeToKick) and 
			(newUsers[key]['timeFailedValidation'] == None)):
				newUsers[key]['timeFailedValidation'] = currentUnixTime
				editRequest = sendRequest(["editMessageText", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'], "text", newUsers[key]['firstName'] + "%20didn%27t press the button in time, and was kicked"])
				if editRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to edit message",newUsers[key]['welcomeMsgid'],editRequest[2])
				# kick user
				kickRequest = sendRequest(["unbanChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key])
				if kickRequest[0] == False:
					# if the kick didn't work, try banning instead
					print("timestamp:", int(time.time()), "Failed to kick, attempting to ban...")
					banRequest = sendRequest(["kickChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key])
					if banRequest[0] == False:
						# if the ban failed, output request contents
						print("timestamp:", int(time.time()), "Couldn't ban user_id", key, ":", banRequest[2])


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
			(currentUnixTime - newUsers[key]['timeJoined'] > unValidatedTimeToKick) and 
			(currentUnixTime - newUsers[key]['timeFailedValidation'] > timeToDelete)) or
			((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == False) and 
			(currentUnixTime - newUsers[key]['timeJoined'] >= validatedTimeToKick) and 
			(newUsers[key]['timeExpiredMessageSendThresh'] != None) and
			(currentUnixTime - newUsers[key]['timeExpiredMessageSendThresh'] > timeToDelete)) or
			((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentBadMessage'] == True) and 
			(newUsers[key]['timeSentBadMessage'] != None) and
			(currentUnixTime - newUsers[key]['timeSentBadMessage'] > timeToDelete))):
				# cleanup messages here
				deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid']])
				if deleteRequest[0] == False:
					print("timestamp:", int(time.time()), "Couldn't delete message", newUsers[key]['welcomeMsgid'], ":", deleteRequest[2])
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
			(currentUnixTime - newUsers[key]['timeJoined'] > validatedTimeToKick) and 
			(newUsers[key]['timeExpiredMessageSendThresh'] == None)):
				newUsers[key]['timeExpiredMessageSendThresh'] = currentUnixTime
				editRequest = sendRequest(["editMessageText", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'], "text", newUsers[key]['firstName'] + "%20didn%27t say anything in the time threshold, and was kicked"])
				if editRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to edit message",newUsers[key]['welcomeMsgid'],editRequest[2])
				# kick user
				kickRequest = sendRequest(["unbanChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key])
				if kickRequest[0] == False:
					# if the kick didn't work, try banning instead
					print("timestamp:", int(time.time()), "Failed to kick, attempting to ban...")
					banRequest = sendRequest(["kickChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key])
					if banRequest[0] == False:
						# if the ban failed, output request contents
						print("timestamp:", int(time.time()), "Couldn't ban user_id", key, ":", banRequest[2])


		# if the user has passed validation, but hasn't sent any messages,
		# is within the validatedTimeToKick, and passed the restriction
		# time, give them text only privilages for their 1st message send
		elif ((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == False) and 
			(newUsers[key]['hasSentBadMessage'] == False) and
			(currentUnixTime - newUsers[key]['timeJoined'] < validatedTimeToKick)):
				if ((currentUnixTime - newUsers[key]['timePassedValidation'] >= timeToRestrict) and 
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
					editRequest = sendRequest(["editMessageText", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'], "text", newUsers[key]['firstName'] + ",%20your restriction time is over!%0A%0APlease send a plaintext message like a hello within the next%20" + str(int(validatedTimeToKick/60)) + "%20minutes, to lift your other restrictions%0A%0A%28I%27d let you send a sticker if the bot API allowed just text and stickers%29%20%3A%29%0A%0ANote%3A Sending any of the following may get you banned - URL, Email, Phone Number, Forwarded Message or a Bot Command"])
					if editRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to edit message",newUsers[key]['welcomeMsgid'],editRequest[2])
					permEditRequest = sendRequest(["restrictChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key, "permissions", newMemberRestrictions, "until_date", currentUnixTime])
					if permEditRequest[0] == True:
						newUsers[key]['hasSetTextRestrictions'] = True
					elif permEditRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to change permissions for", key, ":", permEditRequest[2])



		# if the user has passed validation, but has sent a prohibited message,
		# ban them from group & add time kicked to their newUsers entry 
		# (to know when to delete the msgs)
		elif ((newUsers[key]['passedValidation'] == True) and
			(newUsers[key]['hasSentBadMessage'] == True) and
			(newUsers[key]['timeSentBadMessage'] == None)):
				newUsers[key]['timeSentBadMessage'] = currentUnixTime
				editRequest = sendRequest(["editMessageText", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid'], "text", newUsers[key]['firstName'] + "%20sent something not permitted for their first message, and was banned"])
				if editRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to edit message",newUsers[key]['welcomeMsgid'],editRequest[2])
				banRequest = sendRequest(["kickChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key])
				if banRequest[0] == False:
					# if the ban failed, output request contents
					print("timestamp:", int(time.time()), "Couldn't ban user_id", key, ":", banRequest[2])


		# if the user has passed validation, and has sent a message,
		# delete the join messages & mark them for deletion from the
		# newUsers dictionary
		# And give them all normal privilages permanently
		elif ((newUsers[key]['passedValidation'] == True) and 
			(newUsers[key]['hasSentGoodMessage'] == True)):
				# delete welcome message. Don't delete join message, want to see in past when a genuine user joins the chat
				deleteRequest = sendRequest(["deleteMessage", "chat_id", newUsers[key]['chatId'], "message_id", newUsers[key]['welcomeMsgid']])
				if deleteRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to delete message", newUsers[key]['welcomeMsgid'], ":", deleteRequest[2])
				# mark newUser for deletion from dictionary
				toDelete.append(key)
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
				permEditRequest = sendRequest(["restrictChatMember", "chat_id", newUsers[key]['chatId'], "user_id", key, "permissions", newMemberRestrictions, "until_date", currentUnixTime])
				if permEditRequest[0] == False:
					print("timestamp:", int(time.time()), "Failed to change permissions for", key, ":", permEditRequest[2])


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
	# set initial offset to 0, to make telegram send all new updates
	# pollTimeout -> how long to wait for long poll response in seconds
	msgOffset, pollTimeout = 0, 20
	# initial token value
	token = ""
	argv = sys.argv[1:]

	# dictionary of new users who need to be kept track of until
	# new user requirements are satisfied
	newUsers = {}

	# Chat IDs to work with. Don't want just anyone adding the bot and sucking up the host's resources!
	whiteListRead = readIntFileToList("whitelist.txt")
	if whiteListRead[0] == True:
		usingWhitelistRestrictions = True
		whitelistedChatIDs = whiteListRead[1]
		print("Using whitelist restrictions")
	else:
		usingWhitelistRestrictions = False
		print("Whitelist file not found/processing failed, disabling whitelist restrictions")

	# things to kick a new user for if sent in their 1st text message
	bannedEntities = ['bot_command', 'url', 'email', 'phone_number']

	# unValidatedTimeToKick -> seconds to wait for user to tap button before kicking them
	# timeToRestrict -> seconds to restrict permissions for new user after tapping button
	# validatedTimeToKick -> seconds to keep user in chat after validation without saying anything before kicking
	# timeToDelete -> seconds before deleting sent messages
	unValidatedTimeToKick, timeToRestrict, validatedTimeToKick, timeToDelete = 300, 60, 900, 120

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

	bot_id = json.loads(sendRequest(["getMe"])[2])['result']['id']
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
			# failed to fetch new messages, wait for x seconds then try again
			time.sleep(30)
		

