import discord
import os
import sys
#import asyncio
from datetime import datetime, timezone
from replit import db
from discord import app_commands
from typing import Optional
from discord.ext import tasks
from keep_alive import keep_alive

TEST_DISCORD_GUILD = "Cantiga's server"
TEST_GUILD_ID = 1262832131026194474    # ID of the guild - Cantiga's server
TEST_CHANNEL_ID = 1262832131554545831    # Channel ID of the channel we send the message to

DISCORD_GUILD_PRISON = "Prison Island"
GUILD_ID_PRISON = 1273976720382234675    # ID of the guild - Prison Island
GUILD_BATTLE_CHANNEL_ID = 1274113299314638879 # Channel ID of the channel we send the message to
MAX_ATTEMPTS = 3

DISCORD_GUILD = DISCORD_GUILD_PRISON 
GUILD_ID = GUILD_ID_PRISON 
CHANNEL_ID = GUILD_BATTLE_CHANNEL_ID


intents=discord.Intents.default()
client = discord.Client(intents=discord.Intents.default())
token = os.environ['DISCORD_TOKEN']
tree = app_commands.CommandTree(client)
allowed_guilds = [TEST_DISCORD_GUILD, GUILD_ID_PRISON]
allowed_channel = [TEST_CHANNEL_ID, GUILD_BATTLE_CHANNEL_ID]

#reset at 2 a.m. 0 min 0 sec UTC - which is 7 p.m. PDT
dt = datetime(2024, 8, 28, 2, 0, 0, tzinfo=timezone.utc)
#for testing so I won't need to wait
#dt = datetime(2024, 8, 28, 1, 6, 0, tzinfo=timezone.utc)
eventTime = dt.time()

# Make sure we have our Bot first
if not token:
    print('ERROR: Token var is missing: TOKEN')
    sys.exit(-1)

# Command to update the remaining attempts of a user
@tree.command(name="update", description="Update remaining attempts")#,
#              guild=discord.Object(id=GUILD_ID))
@app_commands.describe(name="The optional argument. If not provided, update member with your discord name")
@app_commands.describe(attempts="The optional argument. If not provided, reduce the attempt by 1")
async def update_command(interaction, name: Optional[str] = None, attempts: Optional[int] = -1):
    if name is None:
        name = interaction.user.name

    update_message = interaction.user.name + " updated remaining attempts for " + name + "."
    current_attempt = getCurrentAttemps(name.lower())
    
    if attempts == -1:
        attempts = current_attempt
        if attempts == -1:
            update_message += "\nCommand failed. User not found. Please register first."
            await interaction.response.send_message(update_message)
            return
        else:
            attempts = attempts - 1

    if attempts < 0:
        attempts = 0

    update_message += "\nPrevious: " + str(current_attempt) + "\nNew: " + str(attempts) + "\n"
    
    if (update_attempts(name, attempts) == False):
        update_message = "ERROR: " + name + " not found"
        
    await interaction.response.send_message(update_message)
    
# Command to show everyone from the database
@tree.command(name="show", description="Show attempts left")#,             guild=discord.Object(id=GUILD_ID))
async def show_command(interaction):
    resp_message = composeRemainingMessage()
    await interaction.response.send_message(resp_message)

# Command to add a guild member to the database
@tree.command(name="add", description="Add a guild member to the database")#,     guild=discord.Object(id=GUILD_ID))
async def add_command(interaction, name: str):
    resp_message = interaction.user.name + " added " + name + " to the battle ranking"
    add_member(name.lower())
    await interaction.response.send_message(resp_message)

# Command to remove a guild member from the database
@tree.command(name="remove", description="Remove a guild member from the database")#,
#     guild=discord.Object(id=GUILD_ID))
async def remove_command(interaction, name: str):
    resp_message = interaction.user.name + " removed " + name + " from the battle ranking"
    delete_member(name.lower())
    await interaction.response.send_message(resp_message)

# Task event that run at eventTime - Reset all attempts
@tasks.loop(time=eventTime)
async def reset_once_a_day():
    reset_attempts()    
    message = "All remaining attempts were reset at (UTC) " + str(datetime.now())
    print(message)
    channel = client.get_channel(CHANNEL_ID)
    await channel.send(message)

# Ready event
@client.event
async def on_ready():
#    await tree.sync(guild=discord.Object(id=guild.id))
    await tree.sync()

    # Print all the keys from the database
    print("Current keys at start: ")
    keys = db.keys()
    print(list(keys)) 

    print("Reset time (UTC) is: " + str(eventTime))

    if not reset_once_a_day.is_running():
        reset_once_a_day.start()  #If the task is not already running, start it.
        print("Reset task started")

# Respond to a message - current not used
@client.event
async def on_message(message):
    if message.author == client.user:
        return
        
# Get current attempt for a member
def getCurrentAttemps(name):
    if name in db.keys():
        return db[name]
    else:
        return -1

# Composes the message to be sent to the channel with all the remaining attempts
# of the key-value pairs in the database
def composeRemainingMessage():
    resp_message = "Remaining attempts for today:\n"
    # Print all the keys from the database
    keys = db.keys()
    
    for key in keys:
        resp_message += key + ": " + str(db[key]) + "\n"
    return resp_message

# Reset all remaining attempts to MAX_ATTEMPTS
def reset_attempts():
    keys = db.keys()
    for key in keys:
        db[key] = MAX_ATTEMPTS

# Update the remaining attempts of a member
def update_attempts(name, attempts):
  if name in db.keys():
    db[name] = attempts

# Add a member to the database
def add_member(name):
    if name not in db:
        db[name] = MAX_ATTEMPTS        

# Remove a member from the database
def delete_member(name):
    del db[name]
    if name not in db:
        print("Value deleted successfully.")        

keep_alive()
client.run(token)
