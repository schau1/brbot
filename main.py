import discord
import os
import sys
#import asyncio
from datetime import datetime, timezone
#from replit import db
from discord import app_commands
from typing import Optional
from discord.ext import tasks
from dotenv import load_dotenv

# Loads the .env file that resides on the same level as the script.
load_dotenv()

TEST_DISCORD_GUILD = "Cantiga's server"
TEST_GUILD_ID = 1262832131026194474    # ID of the guild - Cantiga's server
TEST_CHANNEL_ID = 1262832131554545831    # Channel ID of the channel we send the message to

DISCORD_GUILD_PRISON = "Prison Island"
GUILD_ID_PRISON = 1273976720382234675    # ID of the guild - Prison Island
GUILD_BATTLE_CHANNEL_ID = 1279174345033519166 # Channel ID of the channel we send the message to
MAX_ATTEMPTS = 3

DISCORD_GUILD = DISCORD_GUILD_PRISON 
GUILD_ID = GUILD_ID_PRISON 
CHANNEL_ID = GUILD_BATTLE_CHANNEL_ID

intents=discord.Intents.default()
client = discord.Client(intents=discord.Intents.default())
token = os.getenv('DISCORD_TOKEN')
tree = app_commands.CommandTree(client)
allowed_guilds = [TEST_DISCORD_GUILD, GUILD_ID_PRISON]
allowed_channel = [TEST_CHANNEL_ID, GUILD_BATTLE_CHANNEL_ID]
db = {"cantiga": 3, "akiria": 3, "codz": 3,
      "nico": 3, "elementus": 3, "snoopy": 3, 
      "knights of": 3, "flea": 3, "prinny": 3,
      "chels": 3, "cyber": 3, "domova": 3,
      "lexi": 3, "prinny": 3, "xal": 3,
      "xalxal": 3, "zax": 3, "dk": 3,
      "k1lo": 3, "stelio": 3, "ketch": 3}

#reset at 2 a.m. 0 min 0 sec UTC - which is 7 p.m. PDT
dt = datetime(2024, 8, 28, 2, 0, 0, tzinfo=timezone.utc)
#for testing so I won't need to wait
#dt = datetime(2024, 8, 28, 1, 6, 0, tzinfo=timezone.utc)
eventTime = dt.time()
logFile = None

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
    
    if attempts < 0:
        attempts = current_attempt
        if attempts < 0:
            update_message += "\nCommand failed. User not found. Please register first."
            await interaction.response.send_message(update_message)
            return
        else:
            attempts = attempts - 1
    elif attempts > MAX_ATTEMPTS:
        attempts = MAX_ATTEMPTS
        update_message += "\nExceeding max attempts. Setting attempt to " + str(MAX_ATTEMPTS) + "."

    if attempts < 0:
        attempts = 0

    update_message += "\nPrevious: " + str(current_attempt) + "\nNew: " + str(attempts) + "\n"
    
    if (update_attempts(name, attempts) == False):
        update_message = "\nERROR: " + name + " not found"
        
    logFile.write("\n" + update_message)
    
    await interaction.response.send_message(update_message)
    
# Command to show everyone from the database
@tree.command(name="show", description="Show attempts left")#,             guild=discord.Object(id=GUILD_ID))
async def show_command(interaction):
    resp_message = composeRemainingMessage()
    logFile.write("\n" + resp_message)    
    await interaction.response.send_message(resp_message)

# Command to add a guild member to the database
@tree.command(name="add", description="Add a guild member to the database")#,     guild=discord.Object(id=GUILD_ID))
async def add_command(interaction, name: str):
    resp_message = interaction.user.name + " added " + name + " to the battle ranking"
    if (add_member(name.lower()) == False):
        resp_message = name + " is already in the database"
    logFile.write("\n" + resp_message)
    await interaction.response.send_message(resp_message)

# Command to remove a guild member from the database
@tree.command(name="remove", description="Remove a guild member from the database")#,
#     guild=discord.Object(id=GUILD_ID))
async def remove_command(interaction, name: str):
    resp_message = interaction.user.name + " removed " + name + " from the battle ranking"
    delete_member(name.lower())
    logFile.write("\n" + resp_message)        
    await interaction.response.send_message(resp_message)

# Task event that run at eventTime - Reset all attempts
@tasks.loop(time=eventTime)
async def reset_once_a_day():
    await writeDataToDatabase() # daily writing data to the database
    
    global logFile
    logFile.write("\n\nData before reset:")
    writeData(logFile)    
    logFile.close() # Close old log file and make a new log file    
    
    logFile = open("log_" + str(datetime.now().strftime('%Y-%m-%d')) + ".txt", "a")  
        
    reset_attempts()    
    message = "\nAll remaining attempts were reset at (UTC) " + str(datetime.now())
    print(message)
    logFile.write("\n" + message)
    channel = client.get_channel(CHANNEL_ID)
    await channel.send(message)

@tasks.loop(minutes=5)
async def write_every_hour():
    await writeDataToDatabase() # daily writing data to the database
    
# Ready event
@client.event
async def on_ready():
#    await tree.sync(guild=discord.Object(id=guild.id))
    await tree.sync()

    global logFile
    logFile = open("log_" + str(datetime.now().strftime('%Y-%m-%d')) + ".txt", "a")
    
    # Read keys from the database
    readDataFromDatabase()
    
    # Print all the keys from the database
    logFile.write("\n" + str(datetime.now()) + ": Current keys at start: \n")
    writeData(logFile)
    
    logFile.write("\nReset time (UTC) is: " + str(eventTime))

    if not reset_once_a_day.is_running():
        reset_once_a_day.start()  #If the task is not already running, start it.
        logFile.write("\nReset task started")

    if not write_every_hour.is_running():
        write_every_hour.start()
        logFile.write("\nData writing task started")   


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
    
    for key in sorted(keys):
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
    return True
  else:
    return False

# Add a member to the database
def add_member(name):
    if name not in db:
        db[name] = MAX_ATTEMPTS
        return True
    else:
        return False

# Remove a member from the database
def delete_member(name):
    del db[name]
    if name not in db:
       logFile.write("\n" + name + " deleted successfully.")

def writeData(f):      
    keys = db.keys()
    
    for key in keys:
        data = key + "," + str(db[key]) + "\n"
        f.write(data)

def readDataFromDatabase():
    with open('data.txt') as f:
        lines = f.readlines()
        for line in lines:            
            if line: # if line is not empty
                data = line.split(',')
                db[data[0]] = int(data[1])
    f.close()
    
async def writeDataToDatabase():
    f = open("data.txt", "w")
    writeData(f)
    f.close()   
    
client.run(token)
