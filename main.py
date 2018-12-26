import re
import logging
import datetime
import json
from configparser import ConfigParser
from auth import bot_token
import discord
from discord.ext import commands
from discord.ext.commands import group

config = ConfigParser()
config.read('config.ini')
prefix = config.get('bot', 'CommandPrefix')

bot = commands.Bot(command_prefix=prefix)

## logger shit ##
################################################################################
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s', '%Y-%m-%d %H:%M:%S')

def setup_logger(logger):
	logger.setLevel(logging.DEBUG)

	fh = logging.FileHandler('logs.log')
	fh.setLevel(logging.DEBUG)
	fh.setFormatter(formatter)
	sh = logging.StreamHandler()
	sh.setLevel(logging.INFO)
	sh.setFormatter(formatter)

	def decorate_emit(fn):
		def new(*args):
			levelno = args[0].levelno
			if(levelno >= logging.CRITICAL):
				colour = '\033[1;35m'
			elif(levelno >= logging.ERROR):
				colour = '\033[1;31m'
			elif(levelno >= logging.WARNING):
				colour = '\033[1;33m'
			elif(levelno >= logging.INFO):
				colour = '\033[1;37m'
			elif(levelno >= logging.DEBUG):
				colour = '\033[1;32m'
			else:
				colour = '\033[0;0m'
			args[0].levelname = "{0}{1}\033[0;0m".format(colour, args[0].levelname)

			return fn(*args)
		return new

	sh.emit = decorate_emit(sh.emit)
	logger.addHandler(fh)
	logger.addHandler(sh)

logger = logging.getLogger('main')
setup_logger(logger)
################################################################################

MOD_ROLE = config.get('discord', 'ModRole')

SOLO_CHANNEL_ID = config.getint('discord', 'SoloChannelID')
DUO_CHANNEL_ID = config.getint('discord', 'DuoChannelID')
SQUAD_CHANNEL_ID = config.getint('discord', 'SquadChannelID')

SOLO_GAME_CODES_LIST = []
SOLO_GAME_CODES = []
SOLO_USER_LIST = []
DUO_GAME_CODES_LIST = []
DUO_GAME_CODES = []
DUO_USER_LIST = []
SQUAD_GAME_CODES_LIST = []
SQUAD_GAME_CODES = []
SQUAD_USER_LIST = []

IS_OPEN = 0

FIRST_PLACE_POINTS = config.getint('bot', 'FirstPlacePoints')
SECOND_PLACE_POINTS = config.getint('bot', 'SecondPlacePoints')
THIRD_PLACE_POINTS = config.getint('bot', 'ThirdPlacePoints')

############
# key:
# 1 = solo
# 2 = duo
# 3 = squad
#############
GAME_MODE = 1

##########################################
# embed initialisation for game code list
##########################################
GAME_CODE_EMBED = discord.Embed(color=0x0EBFE9, timestamp=datetime.datetime.utcnow())
GAME_CODE_EMBED.set_author(name="Big Brain Bot", icon_url='https://cdn.discordapp.com/avatars/508616362411819008/1a022b9101a4010ab9dfdc492fbc6e1d.png')
GAME_CODE_EMBED.set_footer(text="Made by Adure#3333")


## HELPER FUNCTIONS ##
################################################################################
###########################################
# calculate score from kills and placement
###########################################
def calculate_score(kills, placement):
	score = 0
	kills = int(kills)
	placement = int(placement)
	if placement == 1:
		score += FIRST_PLACE_POINTS
	elif placement == 2:
		score += SECOND_PLACE_POINTS
	elif placement == 3:
		score += THIRD_PLACE_POINTS

	kills_points = kills / 2
	score += kills_points

	logger.info(f"Score calculation = {score}")

	return score

def clear_lists():
	global SOLO_GAME_CODES_LIST
	global SOLO_GAME_CODES
	global SOLO_USER_LIST
	global DUO_GAME_CODES_LIST
	global DUO_GAME_CODES
	global DUO_USER_LIST
	global SQUAD_GAME_CODES_LIST
	global SQUAD_GAME_CODES
	global SQUAD_USER_LIST

	global GAME_CODE_EMBED

	SOLO_GAME_CODES_LIST = []
	SOLO_GAME_CODES = []
	SOLO_USER_LIST = []
	DUO_GAME_CODES_LIST = []
	DUO_GAME_CODES = []
	DUO_USER_LIST = []
	SQUAD_GAME_CODES_LIST = []
	SQUAD_GAME_CODES = []
	SQUAD_USER_LIST = []

	GAME_CODE_EMBED.clear_fields()
	logger.info("Cleared all user lists")
################################################################################


## BOT COMMANDS ##
################################################################################
#####################################
# changes game mode and clears lists
#####################################
@bot.command()
@commands.has_role(MOD_ROLE)
async def mode(ctx, gameMode):
	"""
	change current scrim game mode
	"""
	global GAME_MODE

	gameMode = gameMode.lower()

	if gameMode == "solo":
		GAME_MODE = 1
		logger.info(f'{ctx.author.name}#{ctx.author.discriminator} changed game mode to {GAME_MODE}')
		await ctx.send("Successfully changed game mode to solo")

		clear_lists()

	elif gameMode == "duo":
		GAME_MODE = 2
		logger.info(f'{ctx.author.name}#{ctx.author.discriminator} changed game mode to {GAME_MODE}')
		await ctx.send("Successfully changed game mode to duo")

		clear_lists()

	elif gameMode == "squad":
		GAME_MODE = 3
		logger.info(f'{ctx.author.name}#{ctx.author.discriminator} changed game mode to {GAME_MODE}')
		await ctx.send("Successfully changed game mode to squad")

		clear_lists()


@bot.command()
async def game(ctx, gamecode):
	"""
	Enter user into game code list of the specified game mode.

	For a unique code it creates a new entry in the list with that user,
	and adds a new field to the game code list embed.
	When entering with a non-unique code,
	it adds the user to the list of users with that game code,
	and updates the game code embed field to add the new user.
	"""
	gamecode = gamecode.lower()
	global IS_OPEN
	if IS_OPEN == 0:
		await ctx.send(f'Scrims are closed at the moment, check back later')
		logger.info(f'game code entering attempt while scrims are closed - {ctx.author.id}')
		return

	global GAME_CODE_EMBED
	GAME_CODE_EMBED.timestamp = datetime.datetime.utcnow()
	###############
	# IF SOLO MODE
	###############
	if GAME_MODE == 1:
		if ctx.author.id in SOLO_USER_LIST:
			logger.error(f'User tried to enter game when already entered - {ctx.author.name}#{ctx.author.discriminator}')
			await ctx.send(f'<@{ctx.author.id}>, You have already entered a game')
			return

		SOLO_USER_LIST.append(ctx.author.id)
		if gamecode not in SOLO_GAME_CODES_LIST:
			SOLO_GAME_CODES_LIST.append(gamecode)
			SOLO_GAME_CODES.append({
				'gamecode': gamecode,
				'users': [ctx.author.id]
			})

			GAME_CODE_EMBED.add_field(name=f"**1 user in game code {gamecode.upper()}**", value=f"<@{ctx.author.id}>", inline=False)

			logger.info(f'{ctx.author.name}#{ctx.author.discriminator} added new gamecode - {gamecode}')
			await ctx.send(f"Added <@{ctx.author.id}> with game code - `{gamecode}`")
		else:
			for items in SOLO_GAME_CODES:
				if items['gamecode'] == gamecode:
					if id not in items['users']:
						items['users'].append(ctx.author.id)

						list = ""
						for e in items['users']:
							list += f"<@{e}>\n"

						for i in SOLO_GAME_CODES_LIST:
							index = SOLO_GAME_CODES_LIST.index(gamecode)

						GAME_CODE_EMBED.set_field_at(index, name=f"**{len(items['users'])} users in game code {gamecode.upper()}**", value=list)

						logger.info(f'Added {ctx.author.name}#{ctx.author.discriminator} to {gamecode} gamecode')
						await ctx.send(f"Added <@{ctx.author.id}> with game code - `{gamecode}`")
					else:
						logger.error(f'User tried to enter with identical gamecode - {ctx.author.name}#{ctx.author.discriminator}')
						await ctx.send(f"<@{ctx.author.id}>, You have already entered with this gamecode")

	##############
	# IF DUO MODE
	##############
	if GAME_MODE == 2:
		if ctx.author.id in DUO_USER_LIST:
			logger.error(f'User tried to enter game when already entered - {ctx.author.name}#{ctx.author.discriminator}')
			await ctx.send(f'<@{ctx.author.id}>, You have already entered a game')
			return

		DUO_USER_LIST.append(ctx.author.id)
		if gamecode not in DUO_GAME_CODES_LIST:
			DUO_GAME_CODES_LIST.append(gamecode)
			DUO_GAME_CODES.append({
				'gamecode': gamecode,
				'users': [ctx.author.id]
			})

			GAME_CODE_EMBED.add_field(name=f"**1 user in game code {gamecode.upper()}**", value=f"<@{ctx.author.id}>", inline=False)

			logger.info(f'{ctx.author.name}#{ctx.author.discriminator} added new gamecode - {gamecode}')
			await ctx.send(f"Added <@{ctx.author.id}> with game code - `{gamecode}`")
		else:
			for items in DUO_GAME_CODES:
				if items['gamecode'] == gamecode:
					if id not in items['users']:
						items['users'].append(ctx.author.id)

						list = ""
						for e in items['users']:
							list += f"<@{e}>\n"

						for i in DUO_GAME_CODES_LIST:
							index = DUO_GAME_CODES_LIST.index(gamecode)

						GAME_CODE_EMBED.set_field_at(index, name=f"**{len(items['users'])} users in game code {gamecode.upper()}**", value=list)

						logger.info(f'Added {ctx.author.name}#{ctx.author.discriminator} to {gamecode} gamecode')
						await ctx.send(f"Added <@{ctx.author.id}> with game code - `{gamecode}`")
					else:
						logger.error(f'User tried to enter with identical gamecode - {ctx.author.name}#{ctx.author.discriminator}')
						await ctx.send(f"<@{ctx.author.id}>, You have already entered with this gamecode")

	################
	# IF SQUAD MODE
	################
	if GAME_MODE == 3:
		if ctx.author.id in SQUAD_USER_LIST:
			logger.error(f'User tried to enter game when already entered - {ctx.author.name}#{ctx.author.discriminator}')
			await ctx.send(f'<@{ctx.author.id}>, You have already entered a game')
			return

		SQUAD_USER_LIST.append(ctx.author.id)
		if gamecode not in SQUAD_GAME_CODES_LIST:
			SQUAD_GAME_CODES_LIST.append(gamecode)
			SQUAD_GAME_CODES.append({
				'gamecode': gamecode,
				'users': [ctx.author.id]
			})

			GAME_CODE_EMBED.add_field(name=f"**1 user in game code {gamecode.upper()}**", value=f"<@{ctx.author.id}>", inline=False)

			logger.info(f'{ctx.author.name}#{ctx.author.discriminator} added new gamecode - {gamecode}')
			await ctx.send(f"Added <@{ctx.author.id}> with game code - `{gamecode}`")
		else:
			for items in SQUAD_GAME_CODES:
				if items['gamecode'] == gamecode:
					if id not in items['users']:
						items['users'].append(ctx.author.id)

						list = ""
						for e in items['users']:
							list += f"<@{e}>\n"

						for i in SQUAD_GAME_CODES_LIST:
							index = SQUAD_GAME_CODES_LIST.index(gamecode)

						GAME_CODE_EMBED.set_field_at(index, name=f"**{len(items['users'])} users in game code {gamecode.upper()}**", value=list)

						logger.info(f'Added {ctx.author.name}#{ctx.author.discriminator} to {gamecode} gamecode')
						await ctx.send(f"Added <@{ctx.author.id}> with game code - `{gamecode}`")
					else:
						logger.error(f'User tried to enter with identical gamecode - {ctx.author.name}#{ctx.author.discriminator}')
						await ctx.send(f"<@{ctx.author.id}>, You have already entered with this gamecode")


@bot.command()
async def score(ctx, kills, placement, gamecode):
	"""
	If a verification image is provided with the command,
	calculate user's score from their inputted kills and placement,
	and update the leaderboard file with the added score.
	"""
	gamecode = gamecode.lower()
	global IS_OPEN
	if IS_OPEN == 0:
		await ctx.send(f'Scrims are closed at the moment, check back later')
		logger.info(f'score entering attempt while scrims are closed - {ctx.author.id}')
		return

	if ctx.message.attachments == []:
		await ctx.send("Please attach a screenshot of your game for verification")
		logger.error(f"Missing game screenshot from {ctx.author.id}")
		return

	global GAME_MODE
	if GAME_MODE == 1:
		global SOLO_GAME_CODES_LIST
		if gamecode not in SOLO_GAME_CODES_LIST:
			await ctx.send(f'You cannot enter a score, you have not entered your game code')
			logger.error(f'Scoring attempt with no associated game code existing - {ctx.author.id}')
			return

		score = calculate_score(kills, placement)

		with open('solo_leaderboard.json', 'r+') as solo_json:
			content = json.load(solo_json)

			for team in content['scores']:
				if team['userId'] == ctx.author.id:
					team['score'] += float(score)
					team['kills'] += int(kills)

			solo_json.seek(0)
			json.dump(content, solo_json, indent=4, sort_keys=True, separators=(',', ': '))
			solo_json.truncate()

			await ctx.send(f"Score: {score}, added to player <@{ctx.author.id}> with Kills: {kills}, Placement: {placement} and GameNumber: {gamecode}")
			logger.info(f"Score: {score}, added to player <@{ctx.author.id}> with Kills: {kills}, Placement: {placement} and GameNumber: {gamecode}")

	if GAME_MODE == 2:
		global DUO_GAME_CODES_LIST
		if gamecode not in DUO_GAME_CODES_LIST:
			await ctx.send(f'You cannot enter a score, you have not entered your game code')
			logger.error(f'Scoring attempt with no associated game code existing - {ctx.author.id}')
			return

		score = calculate_score(kills, placement)

		with open('duo_leaderboard.json', 'r+') as duo_json:
			content = json.load(duo_json)

			for team in content['scores']:
				if team['owner'] == ctx.author.id:
					team['score'] += float(score)
					team['kills'] += int(kills)

			duo_json.seek(0)
			json.dump(content, duo_json, indent=4, sort_keys=True, separators=(',', ': '))
			duo_json.truncate()

			await ctx.send(f"Score: {score}, added to team ")

	if GAME_MODE == 3:
		global SQUAD_GAME_CODES_LIST
		if gamecode not in SQUAD_GAME_CODES_LIST:
			await ctx.send(f'You cannot enter a score, you have not entered your game code')
			logger.error(f'Scoring attempt with no associated game code existing - {ctx.author.id}')
			return

		score = calculate_score(kills, placement)

		with open('squad_leaderboard.json', 'r+') as squad_json:
			content = json.load(squad_json)

			for team in content['scores']:
				if team['owner'] == ctx.author.id:
					team['score'] += float(score)
					team['kills'] += int(kills)

			squad_json.seek(0)
			json.dump(content, squad_json, indent=4, sort_keys=True, separators=(',', ': '))
			squad_json.truncate()

@bot.group(invoke_without_command=True)
async def team(ctx, mode, teamname = None, *users):
	"""
	Use '/help team' for info on how to use this command.
	"""
	pass

@team.command(name="delete")
async def team_delete(ctx):
	""" - Delete your team. Use '/help team delete' for more info.
	Coming soon :)
	"""
	pass

@team.command(name="leave")
async def team_leave(ctx):
	""" - Leave your team. Use '/help team leave' for more info.
	Coming soon :)
	"""
	pass

@team.command(name="invite")
async def team_invite(ctx, *users):
	""" - Invite a user to your team. Use '/help team invite' for more info.
	Coming soon :)
	"""
	pass

@team.command(name="accept")
async def team_accept(ctx):
	""" - Accept a team invitation. Use '/help team accept' for more info.
	Coming soon :)
	"""
	pass

@team.command(name="decline")
async def team_decline(ctx):
	""" - Decline a team invitation. Use '/team help decline' for more info.
	Coming soon :)
	"""
	pass

@team.command(name="create")
async def team_create(ctx, mode, teamname = None, *users):
	"""- Create a team. Use '/help team create' for more info.
	Add either 'solo', 'duo', or 'squad', after 'create' to select which mode to create the team for.
	If entering as a solo no team name is required. For duo and squad,
	add your team name like this: "cool team", and ping your team mates to add them to the team.
	"""
	if mode == "solo":
		with open('solo_leaderboard.json', 'r+') as solo_json:
			soloData = json.load(solo_json)

			for team in soloData['scores']:
				if team['userId'] == ctx.author.id:
					await ctx.send(f'You have already created a team, <@{ctx.author.id}>')
					logger.error(f'Duplicate solo team create attempt - {ctx.author.id}')
					return

			userId = ctx.author.id
			userName = f'{ctx.author.name}#{ctx.author.discriminator}'

			dataDict = {
				'userId': userId,
				'userName': userName,
				'score': 0,
				'kills': 0
			}

			soloData['scores'].append(dataDict)

			solo_json.seek(0)
			json.dump(soloData, solo_json, indent=4, sort_keys=True, separators=(',', ': '))
			solo_json.truncate()

			await ctx.send(f"Successfully created solo team as <@{userId}>")
			logger.info(f"Created solo team as - {userName}")

	#####################
	# CREATE DUO TEAM
	#####################
	if mode == "duo":
		if len(users) > 1:
			await ctx.send(f"Too many users, <@{ctx.author.id}>")
			logger.error(f"Too many users on duo team create attempt - {ctx.author.id}")
			return
		elif len(users) < 1:
			await ctx.send(f"Please ping your team mate when creating your team")
			logger.error(f"No team mate supplied on duo team create attempt - {ctx.author.id}")
			return

		with open('duo_leaderboard.json', 'r+') as duo_json:
			duoData = json.load(duo_json)

			for team in duoData['scores']:
				if team['owner'] == ctx.author.id:
					await ctx.send(f'You have already created a team, <@{ctx.author.id}>')
					logger.error(f'Duplicate duo team create attempt - {ctx.author.id}')
					return

			for team in duoData['scores']:
				if team['teamname'] == teamname:
					await ctx.send(f'That team name is already in use!')
					logger.error(f'Duo team creation attempt with duplicate team name - {ctx.author.id}')
					return

			userList = []
			userListNames = []
			for user in users:
				toArray = re.sub("[^0-9]", "", user)
				userList.append(int(toArray))
			userList.append(ctx.author.id)

			for user in userList:
				_user = await bot.get_user_info(user)
				userName = f'{_user.name}#{_user.discriminator}'
				userListNames.append(userName)

			dataDict = {
				'owner': ctx.author.id,
				'teamname': teamname,
				'memberIds': userList,
				'memberNames': userListNames,
				'score': 0,
				'kills': 0
			}
			duoData['scores'].append(dataDict)

			duo_json.seek(0)
			json.dump(duoData, duo_json, indent=4, sort_keys=True, separators=(',', ': '))
			duo_json.truncate()

			await ctx.send(f"Successfully created duo team with team name `{teamname}` and users {users}")
			logger.info(f"Created duo team - {teamname}, with users - {userList}")

	#####################
	# CREATE SQUAD TEAM
	#####################
	if mode == "squad":
		if len(users) > 3:
			await ctx.send(f"Too many users, <@{ctx.author.id}>")
			logger.error(f"Too many users on squad team create attempt - {ctx.author.id}")
			return
		elif len(users) < 3:
			await ctx.send(f"Please ping all your team mates when creating your team")
			logger.error(f"Not enough team mates supplied on squad team create attemt - {ctx.author.id}")
			return

		with open('squad_leaderboard.json', 'r+') as squad_json:
			squadData = json.load(squad_json)

			for team in squadData['scores']:
				if team['owner'] == ctx.author.id:
					await ctx.send(f'You have already created a team, <@{ctx.author.id}>')
					logger.error(f'Duplicate squad team create attempt - {ctx.author.id}')
					return

			for team in squadData['scores']:
				if team['teamname'] == teamname:
					await ctx.send(f'That team name is already in use!')
					logger.error(f'Squad team creation attempt with duplicate team name - {ctx.author.id}')
					return

			userList = []
			userListNames = []
			for user in users:
				toArray = re.sub("[^0-9]", "", user)
				userList.append(int(toArray))
			userList.append(ctx.author.id)

			for user in userList:
				_user = await bot.get_user_info(user)
				userName = f'{_user.name}#{_user.discriminator}'
				userListNames.append(userName)

			dataDict = {
				'owner': ctx.author.id,
				'teamname': teamname,
				'memberIds': userList,
				'memberNames': userListNames,
				'score': 0,
				'kills': 0
			}
			squadData['scores'].append(dataDict)

			squad_json.seek(0)
			json.dump(squadData, squad_json, indent=4, sort_keys=True, separators=(',', ': '))
			squad_json.truncate()

			await ctx.send(f"Successfully created squad team with team name `{teamname}` and users {users}")
			logger.info(f"Created squad team - {teamname}, with users - {userList}")

#####################
# open game entering
####################
@bot.command(name='open')
@commands.has_role(MOD_ROLE)
async def _open(ctx):
	"""
	opens the scrims
	"""
	global IS_OPEN
	IS_OPEN = 1
	await ctx.send(f'Scrims opened!')
	logger.info(f'Scrims opened by - {ctx.author.id}')

#####################
# close game entering
#####################
@bot.command()
@commands.has_role(MOD_ROLE)
async def close(ctx):
	"""
	closes the scrims
	"""
	global IS_OPEN
	IS_OPEN = 0
	await ctx.send(f'Scrims closed!')
	logger.info(f'Scrims closed by - {ctx.author.id}')

#################
# start the game
#################
@bot.command()
@commands.has_role(MOD_ROLE)
async def start(ctx):
	"""
	open scrims; join voice channel and play game starting mp3
	"""
	global IS_OPEN
	IS_OPEN = 1

	if not discord.opus.is_loaded():
		discord.opus.load_opus('opus')

	global GAME_MODE
	if GAME_MODE == 1:
		channel = bot.get_channel(SOLO_CHANNEL_ID)
	elif GAME_MODE == 2:
		channel = bot.get_channel(DUO_CHANNEL_ID)
	elif GAME_MODE == 3:
		channel = bot.get_channel(SQUAD_CHANNEL_ID)

	try:
		global voice
		voice = await channel.connect(timeout=60, reconnect=True)
		logger.info(f"Bot connected to channel {channel}")
	except discord.ClientException:
		logger.error(f"Bot tried to join {channel}, but is already in it")
	except discord.InvalidArgument:
		logger.error(f"Bot tried to join the channel but it doesnt exist")

	voice.play(discord.FFmpegPCMAudio('./game_starting.mp3'))
	logger.info(f"Game started in gamemode {GAME_MODE}")


## DEBUGGING COMMANDS ##
################################################################################
#######################
# clear the user lists
#######################
@bot.command()
@commands.has_role(MOD_ROLE)
async def clear(ctx):
	"""
	clear all modes user and game code lists
	"""
	clear_lists()

########################
# shows user list embed
########################
@bot.command()
async def users(ctx):
	"""
	display user and game code list
	"""
	await ctx.send(embed=GAME_CODE_EMBED)


## ERROR HANDLERS ##
################################################################################
#################################
# error handler for game command
#################################
@game.error
async def game_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		logger.error(f'Game command missing gamecode - {ctx.author.name}#{ctx.author.discriminator}')
		await ctx.send("Command missing gamecode")
	else:
		logger.error(error)

###################################
# error handler for score command
###################################
@score.error
async def score_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		logger.error(f'Score command is missing parameters - {ctx.author.name}#{ctx.author.discriminator}')
		await ctx.send("Command is missing parameters")
	else:
		logger.error(error)

###################################
# error handler for create command
###################################
@team.error
async def create_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		logger.error(f'Team creation command missing parameters - {ctx.author.name}#{ctx.author.discriminator}')
		await ctx.send("Team creation command missing parameters")
	else:
		logger.error(error)

###################################
# error handler for mode command
###################################
@mode.error
async def mode_error(ctx, error):
	global GAME_MODE
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(f"Current game mode: {GAME_MODE}")
	else:
		logger.error(error)

#################################
# general command error handler
#################################
@bot.listen("on_command_error")
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		return
	else:
		logger.error(error)
################################################################################

#####################
# bot on ready event
#####################
@bot.event
async def on_ready():
	logger.info(f'Logged in as {bot.user.name} - {bot.user.id}')
	game = discord.Game(name='https://www.adure.me')
	await bot.change_presence(activity=game)

#########
# run it
#########
if __name__ == '__main__':
	bot.run(bot_token)