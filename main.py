import re
import logging
import datetime
import json
from pytz import timezone
import pytz
import itertools
from auth import bot_token
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='/')

## logger shit ##
################################################################################
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s',
							'%Y-%m-%d %H:%M:%S')
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

MOD_ROLE = 'Moderator'

SOLO_CHANNEL_ID = 496188599079796736
DUO_CHANNEL_ID = 496188621309739009
SQUAD_CHANNEL_ID = 496188647033536513

SOLO_GAME_CODES_LIST = []
SOLO_GAME_CODES = []
SOLO_USER_LIST = []
DUO_GAME_CODES_LIST = []
DUO_GAME_CODES = []
DUO_USER_LIST = []
SQUAD_GAME_CODES_LIST = []
SQUAD_GAME_CODES = []
SQUAD_USER_LIST = []

FIRST_PLACE_POINTS = 3
SECOND_PLACE_POINTS = 2
THIRD_PLACE_POINTS = 1

############
# key:
# 1 = solo
# 2 = duo
# 3 = squad
#############
global GAME_MODE
GAME_MODE = 1

##########################################
# embed initialisation for game code list
##########################################
GAME_CODE_EMBED = discord.Embed(color=0x0EBFE9, timestamp=datetime.datetime.utcnow())
GAME_CODE_EMBED.set_author(name="Aran's Bot", icon_url='https://avatars2.githubusercontent.com/u/8254643?s=460&v=4')
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

################################################################################


## BOT COMMANDS ##
################################################################################
#####################################
# changes game mode and clears lists
#####################################
@bot.command()
@commands.has_role(MOD_ROLE)
async def mode(ctx, gameMode):
	global GAME_MODE
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
	gameMode = gameMode.lower()

	if gameMode == "solo":
		GAME_MODE = 1
		logger.info(f'{ctx.author.name}#{ctx.author.discriminator} changed game mode to {GAME_MODE}')
		await ctx.send("Successfully changed game mode to solo")

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

	elif gameMode == "duo":
		GAME_MODE = 2
		logger.info(f'{ctx.author.name}#{ctx.author.discriminator} changed game mode to {GAME_MODE}')
		await ctx.send("Successfully changed game mode to duo")

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

	elif gameMode == "squad":
		GAME_MODE = 3
		logger.info(f'{ctx.author.name}#{ctx.author.discriminator} changed game mode to {GAME_MODE}')
		await ctx.send("Successfully changed game mode to squad")

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


##############################################
# let user enter into the game using gamecode.
# enters them into the gamemode that has been -
# selected by mods
##############################################
@bot.command()
async def game(ctx, gamecode):
	global GAME_CODE_EMBED
	GAME_CODE_EMBED.timestamp = datetime.datetime.utcnow()
	###############
	# IF SOLO MODE
	###############
	if GAME_MODE == 1:
		if ctx.author.id not in SOLO_USER_LIST:
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

		else:
			logger.error(f'User tried to enter game when already entered - {ctx.author.name}#{ctx.author.discriminator}')
			await ctx.send(f'<@{ctx.author.id}>, You have already entered a game')

		print(SOLO_GAME_CODES_LIST)
		print(SOLO_GAME_CODES)

	##############
	# IF DUO MODE
	##############
	if GAME_MODE == 2:
		if ctx.author.id not in DUO_USER_LIST:
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

		else:
			logger.error(f'User tried to enter game when already entered - {ctx.author.name}#{ctx.author.discriminator}')
			await ctx.send(f'<@{ctx.author.id}>, You have already entered a game')

		print(DUO_GAME_CODES_LIST)
		print(DUO_GAME_CODES)

	################
	# IF SQUAD MODE
	################
	if GAME_MODE == 3:
		if ctx.author.id not in SQUAD_USER_LIST:
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

		else:
			logger.error(f'User tried to enter game when already entered - {ctx.author.name}#{ctx.author.discriminator}')
			await ctx.send(f'<@{ctx.author.id}>, You have already entered a game')

		print(SQUAD_GAME_CODES_LIST)
		print(SQUAD_GAME_CODES)

###################
# enter user score
###################
@bot.command()
async def score(ctx, kills, placement, gamecode):
	if ctx.message.attachments == []:
		await ctx.send("Please attach a screenshot of your game for verification")
		logger.error(f"Missing game screenshot from {ctx.author.id}")

		return

	global GAME_MODE
	if GAME_MODE == 1:
		score = calculate_score(kills, placement)

		with open('solo_leaderboard.json', 'r+') as solo_json:
			content = json.load(solo_json)

			for team in content['scores']:
				if team['user'] == ctx.author.id:
					team['score'] += score

			solo_json.seek(0)
			json.dump(content, solo_json, indent=4, sort_keys=True, separators=(',', ': '))
			solo_json.truncate()

			await ctx.send(f"Score: {score}, added to player <@{ctx.author.id}> with Kills: {kills}, Placement: {placement} and GameNumber: {gamecode}")
			logger.info(f"Score: {score}, added to player <@{ctx.author.id}> with Kills: {kills}, Placement: {placement} and GameNumber: {gamecode}")

	if GAME_MODE == 2:
		score = calculate_score(kills, placement)

		with open('duo_leaderboard.json', 'r+') as duo_json:
			content = json.load(duo_json)

			for team in content['scores']:
				if team['owner'] == ctx.author.id:
					team['score'] += score
					teamname = team['teamname']

			duo_json.seek(0)
			json.dump(content, duo_json, indent=4, sort_keys=True, separators=(',', ': '))
			duo_json.truncate()

			await ctx.send(f"Score: {score}, added to team ")

	if GAME_MODE == 3:
		score = calculate_score(kills, placement)

		with open('squad_leaderboard.json', 'r+') as squad_json:
			content = json.load(squad_json)

			for team in content['scores']:
				if team['owner'] == ctx.author.id:
					team['score'] += score

			squad_json.seek(0)
			json.dump(content, squad_json, indent=4, sort_keys=True, separators=(',', ': '))
			squad_json.truncate()

##############################################
# create team for either duo or squad
# with a team name and the users in the team
# users have to be entered with a ping
##############################################
@bot.command()
async def create(ctx, mode, teamname = None, *users):
	if mode == "solo":
		with open('solo_leaderboard.json', 'r+') as solo_json:
			soloData = json.load(solo_json)
			user = ctx.author.id

			dataDict = {
				'user': user,
				'score': 0
			}

			soloData['scores'].append(dataDict)

			solo_json.seek(0)
			json.dump(soloData, solo_json, indent=4, sort_keys=True, separators=(',', ': '))
			solo_json.truncate()

			await ctx.send(f"Successfully created solo team as <@{user}>")
			logger.info(f"Created solo team as - {user}")

	#####################
	# CREATE DUO TEAM
	#####################
	if mode == "duo":
		if len(users) > 1:
			await ctx.send(f"Too many users, <@{ctx.author.id}>")
			logger.error(f"Too many users on duo team create attempt - {ctx.author.id}")
			return

		with open('duo_leaderboard.json', 'r+') as duo_json:
			duoData = json.load(duo_json)
			userList = []
			for user in users:
				toArray = re.sub("[^0-9]", "", user)
				userList.append(toArray)

			userList.append(ctx.author.id)

			dataDict = {
				'owner': ctx.author.id,
				'teamname': teamname,
				'members': userList,
				"score": 0
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

		with open('squad_leaderboard.json', 'r+') as squad_json:
			squadData = json.load(squad_json)
			userList = []
			for user in users:
				toArray = re.sub("[^0-9]", "", user)
				userList.append(toArray)

			userList.append(ctx.author.id)

			dataDict = {
				'owner': ctx.author.id,
				'teamname': teamname,
				'members': userList,
				"score": 0
			}
			squadData['scores'].append(dataDict)

			squad_json.seek(0)
			json.dump(squadData, squad_json, indent=4, sort_keys=True, separators=(',', ': '))
			squad_json.truncate()

			await ctx.send(f"Successfully created squad team with team name `{teamname}` and users {users}")
			logger.info(f"Created squad team - {teamname}, with users - {userList}")

#################
# start the game
#################
@bot.command()
@commands.has_role(MOD_ROLE)
async def start(ctx):
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
async def clear(ctx):
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

########################
# shows user list embed
########################
@bot.command()
async def users(ctx):
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

#########
# run it
#########
if __name__ == '__main__':
	bot.run(bot_token)