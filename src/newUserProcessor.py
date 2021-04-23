import time
from uData import uData
from configHandler import configHandler
from tMsgSender import tMsgSender

class newUserProcessor:
	def __init__(self, configHandler, uData, tMsgSender):
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender

	def processNewUserList(self):
		currentUnixTime = int(time.time())
		# iterate over newUsers dictionary, checking if anyone needs kicking
		toDelete = []
		for key in self.uData.getnewUserKeys():
			# get user data, saves making lots of user data requests
			userData = self.uData.getAllUserData(key)
			# get group info for the user, saves making lots of getConfig requests
			groupInfo = self.configHandler.getCustomGroupConfig(userData['chatId'])

			# if the user hasn't passed validation, and
			# has been in chat longer than the kick duration, 
			# and hasn't already got a failed verfication time,
			# kick them, and add the time they were kicked to
			# their newUsers entry (to know when to delete the msgs)
			if ((userData['passedValidation'] == False) and 
				(currentUnixTime - userData['timeJoined'] > groupInfo['unValidatedTimeToKick']) and 
				(userData['timeFailedValidation'] == None)):
					userData['timeFailedValidation'] = currentUnixTime

					# send new message. If that succeeds, add it to current messages 
					# shown in chat, then try and delete the last message sent
					newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", userData['firstName'] + "%20didn%27t press the button in time, and was kicked"])
					if newTextMessageRequest[0] == True:
						userData['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'].pop(len(userData['welcomeMsgid'])-2)])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message:", deleteRequest[2])
					# kick user
					kickRequest = self.tMsgSender.sendRequest(["unbanChatMember", "chat_id", userData['chatId'], "user_id", userData['id']])
					if kickRequest[0] == False:
						# if the kick didn't work, try banning instead
						print("timestamp:", int(time.time()), "Failed to kick, attempting to ban...")
						banRequest = self.tMsgSender.sendRequest(["kickChatMember", "chat_id", userData['chatId'], "user_id", userData['id']])
						if banRequest[0] == False:
							# if the ban failed, output request contents
							print("timestamp:", int(time.time()), "Couldn't ban user_id", userData['id'], ":", banRequest[2])


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
			elif (((userData['passedValidation'] == False) and 
				(currentUnixTime - userData['timeJoined'] > groupInfo['unValidatedTimeToKick']) and 
				(currentUnixTime - userData['timeFailedValidation'] > groupInfo['timeToDelete'])) or
				((userData['passedValidation'] == True) and 
				(userData['hasSentGoodMessage'] == False) and 
				(currentUnixTime - userData['timeJoined'] >= groupInfo['validatedTimeToKick']) and 
				(userData['timeExpiredMessageSendThresh'] != None) and
				(currentUnixTime - userData['timeExpiredMessageSendThresh'] > groupInfo['timeToDelete'])) or
				((userData['passedValidation'] == True) and 
				(userData['hasSentBadMessage'] == True) and 
				(userData['timeSentBadMessage'] != None) and
				(currentUnixTime - userData['timeSentBadMessage'] > groupInfo['timeToDelete']))):
					# cleanup messages here
					for msg in range(len(userData['welcomeMsgid'])):
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'][msg-1]])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message", userData['welcomeMsgid'][msg-1], ":", deleteRequest[2])
					deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['joinedMessage']])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Couldn't delete message", userData['joinedMessage'], ":", deleteRequest[2])
					# mark newUser for deletion from dictionary
					toDelete.append(key)


			# if the user has passed validation, but hasn't sent any messages
			# for longer than the validatedTimeToKick time, assume they are
			# a bot (or not interested), kick them and add the time they were
			# kicked to their newUsers entry (to know when to delete the msgs)
			elif ((userData['passedValidation'] == True) and 
				(userData['hasSentGoodMessage'] == False) and 
				(userData['hasSentBadMessage'] == False) and
				(currentUnixTime - userData['timeJoined'] > groupInfo['validatedTimeToKick']) and 
				(userData['timeExpiredMessageSendThresh'] == None)):
					userData['timeExpiredMessageSendThresh'] = currentUnixTime

					# send new message. If that succeeds, add it to current messages 
					# shown in chat, then try and delete the last message sent
					newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", userData['firstName'] + "%20didn%27t say anything in the time threshold, and was kicked"])
					if newTextMessageRequest[0] == True:
						userData['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'].pop(len(userData['welcomeMsgid'])-2)])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message:", deleteRequest[2])
					
					# kick user
					kickRequest = self.tMsgSender.sendRequest(["unbanChatMember", "chat_id", userData['chatId'], "user_id", userData['id']])
					if kickRequest[0] == False:
						# if the kick didn't work, try banning instead
						print("timestamp:", int(time.time()), "Failed to kick, attempting to ban...")
						banRequest = self.tMsgSender.sendRequest(["kickChatMember", "chat_id", userData['chatId'], "user_id", userData['id']])
						if banRequest[0] == False:
							# if the ban failed, output request contents
							print("timestamp:", int(time.time()), "Couldn't ban user_id", userData['id'], ":", banRequest[2])


			# if the user has passed validation, but hasn't sent any messages,
			# is within the validatedTimeToKick, and passed the restriction
			# time, give them text only privilages for their 1st message send
			elif ((userData['passedValidation'] == True) and 
				(userData['hasSentGoodMessage'] == False) and 
				(userData['hasSentBadMessage'] == False) and
				(currentUnixTime - userData['timeJoined'] < groupInfo['validatedTimeToKick'])):
					if ((currentUnixTime - userData['timePassedValidation'] >= groupInfo['timeToRestrict']) and 
						(userData['hasSetTextRestrictions'] == False)):
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
						if userData['username'] != None:
							newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", "@" + userData['username'] + ",%20your restriction time is over!%0A%0APlease send a plain text message like a hello within the next%20" + str(int(groupInfo['validatedTimeToKick']/60)) + "%20minutes, to lift your other restrictions%0A%0A%28I%27d let you send a sticker if the bot API allowed just text and stickers%29%20%3A%29%0A%0ANote%3A Sending any of the following may get you banned - URL, Email, Phone Number, Forwarded Message, Contact, Location or a Bot Command", "entities", "[{'type':'mention', 'offset':0, 'length':" + str(len(userData['username'])) + "}]"])
						else:
							newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", userData['firstName'] + ",%20your restriction time is over!%0A%0APlease send a plain text message like a hello within the next%20" + str(int(groupInfo['validatedTimeToKick']/60)) + "%20minutes, to lift your other restrictions%0A%0A%28I%27d let you send a sticker if the bot API allowed just text and stickers%29%20%3A%29%0A%0ANote%3A Sending any of the following may get you banned - URL, Email, Phone Number, Forwarded Message, Contact, Location or a Bot Command"])
						if newTextMessageRequest[0] == True:
							userData['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
							deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'].pop(len(userData['welcomeMsgid'])-2)])
							if deleteRequest[0] == False:
								print("timestamp:", int(time.time()), "Failed to delete message:", deleteRequest[2])
						
						permEditRequest = self.tMsgSender.sendRequest(["restrictChatMember", "chat_id", userData['chatId'], "user_id", userData['id'], "permissions", newMemberRestrictions, "until_date", currentUnixTime])
						if permEditRequest[0] == True:
							userData['hasSetTextRestrictions'] = True
							userData['timeSetTextRestrictions'] = currentUnixTime
						elif permEditRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to change permissions for", userData['id'], ":", permEditRequest[2])



			# if the user has passed validation, but has sent a prohibited message,
			# ban them from group & add time kicked to their newUsers entry 
			# (to know when to delete the msgs)
			elif ((userData['passedValidation'] == True) and
				(userData['hasSentBadMessage'] == True) and
				(userData['timeSentBadMessage'] == None)):
					userData['timeSentBadMessage'] = currentUnixTime

					# delete all messages the user has sent, since joining the chat
					for userMessage in userData['sentMessages']:
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userMessage])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Couldn't delete message ID", userMessage, ":", deleteRequest[2])

					# send new message. If that succeeds, add it to current messages 
					# shown in chat, then try and delete the last message sent
					newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", userData['firstName'] + "%20sent something not permitted for their first message, and was banned"])
					if newTextMessageRequest[0] == True:
						userData['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'].pop(len(userData['welcomeMsgid'])-2)])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message:", deleteRequest[2])
					
					banRequest = self.tMsgSender.sendRequest(["kickChatMember", "chat_id", userData['chatId'], "user_id", userData['id']])
					if banRequest[0] == False:
						# if the ban failed, output request contents
						print("timestamp:", int(time.time()), "Couldn't ban user_id", userData['id'], ":", banRequest[2])



			# if the user has passed validation, and has sent a message,
			# give them all normal privilages permanently
			elif ((userData['passedValidation'] == True) and 
				(userData['hasSentGoodMessage'] == True) and
				userData['timeLiftedRestrictions'] == None):
					userData['timeLiftedRestrictions'] = currentUnixTime
					
					# send new message. If that succeeds, add it to current messages 
					# shown in chat, then try and delete the last message sent
					if userData['username'] != None:
						newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", "Welcome @" + userData['username'] + "%21 %0A%0APlease refrain from sending any forwarded messages, locations or contacts here for another " + str(int((groupInfo['timeToRestrictForwards']/60)+1)) + " minutes%21 %28When this message is deleted%29", "entities", "[{'type':'mention', 'offset':8, 'length':" + str(len(userData['username'])) + "}]"])
					else:
						newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", userData['chatId'], "text", "Welcome " + userData['firstName'] + "%21 %0A%0APlease refrain from sending any forwarded messages, locations or contacts here for another " + str(int((groupInfo['timeToRestrictForwards']/60)+1)) + " minutes%21 %28When this message is deleted%29"])
					if newTextMessageRequest[0] == True:
						userData['welcomeMsgid'].append(json.loads(newTextMessageRequest[2])['result']['message_id'])
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'].pop(len(userData['welcomeMsgid'])-2)])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message:", deleteRequest[2])

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

					permEditRequest = self.tMsgSender.sendRequest(["restrictChatMember", "chat_id", userData['chatId'], "user_id", userData['id'], "permissions", newMemberRestrictions, "until_date", currentUnixTime])
					if permEditRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to change permissions for", userData['id'], ":", permEditRequest[2])


			# if the user has passed validation, sent a message, 
			# has already had their restrictions lifted and sent
			# their 1st msg longer than timeToRestrictForwards seconds
			# ago (+ 1 minute for safety like the message),
			# delete the welcome messages and mark them for deletion
			# from newUsers dictionary
			elif ((userData['passedValidation'] == True) and 
				(userData['hasSentGoodMessage'] == True) and
				(userData['timeLiftedRestrictions'] != None) and
				(currentUnixTime - userData['timeSentFirstMessage'] > groupInfo['timeToRestrictForwards'] + 60)):

					# delete welcome message. Don't delete join message, want to see in past when a genuine user joins the chat
					for msg in range(len(userData['welcomeMsgid'])):
						deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", userData['chatId'], "message_id", userData['welcomeMsgid'][msg-1]])
						if deleteRequest[0] == False:
							print("timestamp:", int(time.time()), "Failed to delete message", userData['welcomeMsgid'], ":", deleteRequest[2])
					
					# mark newUser for deletion from dictionary
					toDelete.append(key)


		# delete kicked users from the newUsers table
		for user in toDelete:
			try:
				self.uData.deleteNewUser(user)
			except Exception as e:
				print("timestamp:", int(time.time()), "Failed to remove user", user, ":", str(e))