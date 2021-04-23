class tNewChatMember:
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
					tMsgSender.sendRequest(["restrictChatMember", "chat_id", self.chat_id, "user_id", member['id'], "permissions", newMemberRestrictions, "until_date", self.date])
					# add user to newUser list
					self.addToList(member)
			# if group is in lockdown mode, auto-ban every new user join
			else:
				banRequest = tMsgSender.sendRequest(["kickChatMember", "chat_id", self.chat['id'], "user_id", member['id']])
				if banRequest[0] == False:
					# if the ban failed, output request contents
					print("timestamp:", int(time.time()), "Couldn't ban user_id", member['id'], ":", banRequest[2])
				deleteRequest = tMsgSender.sendRequest(["deleteMessage", "chat_id", self.chat['id'], "message_id", self.message_id])
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
			welcome = tMsgSender.sendRequest(["sendMessage", "chat_id", self.chat_id, "text", welcomeMsg, "entities", "[{'type':'mention', 'offset':6, 'length':" + str(len(member['username'])) + "}]" ,"reply_markup", verifyPrompt])
		else:
			welcomeMsg = "Hiya, " + newUsers[member['id'] + self.chat['id']]['firstName'] + "%0A%0ATo proceed, please tap the %27I%27m not a robot%21%27 button, within the next%20" + str(int(config.getCustomGroupConfig(self.chat['id'])['unValidatedTimeToKick']/60)) + "%20minutes!%0A%0AOnce done, you%27ll have around%20" + str(config.getCustomGroupConfig(self.chat['id'])['timeToRestrict']) + "%20seconds of full restrictions, then%20" + str(int(config.getCustomGroupConfig(self.chat['id'])['validatedTimeToKick']/60)) + "%20minutes to send a message%20%3A%29"
			# send welcomeverify prompt to user
			welcome = tMsgSender.sendRequest(["sendMessage", "chat_id", self.chat_id, "text", welcomeMsg, "reply_markup", verifyPrompt])
		if welcome[0] == True:
			# add message id of the welcome message, to know what message
			# to modify/delete later on
			#newUsers[member['id'] + self.chat['id']]['welcomeMsgid'] = json.loads(welcome[2])['result']['message_id']
			newUsers[member['id'] + self.chat['id']]['welcomeMsgid'].append(json.loads(welcome[2])['result']['message_id'])
