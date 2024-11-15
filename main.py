from curses.ascii import isdigit
from re import I
import re
import discord
import os
import sys
#import asyncio
import time
from datetime import datetime, timezone
#from replit import db
from discord import app_commands
from typing import Optional
from discord.ext import tasks
from dotenv import load_dotenv
from prettytable import PrettyTable

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

db = {}
timedb = {}

#reset at 2 a.m. 0 min 0 sec UTC - which is 7 p.m. PDT
dt = datetime(2024, 8, 28, 2, 0, 0, tzinfo=timezone.utc)
#for testing so I won't need to wait
#dt = datetime(2024, 8, 28, 1, 6, 0, tzinfo=timezone.utc)
eventTime = dt.time()
logFile = None
assignmentLink = None

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
        name = interaction.user.global_name

    update_message = interaction.user.global_name + " updated remaining attempts for " + name + "."
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
    
    if (update_attempts(name.lower(), attempts) == False):
        update_message = "\nERROR: '" + name + "' not found"
        
    logFile.write("\n" + update_message)
    
    await interaction.response.send_message(update_message)
    
# Command to update the remaining attempts of a user
@tree.command(name="readt", description="Read a new timeslot file")#,
async def readtimeslot_command(interaction):
    update_message = interaction.user.global_name + " updated timeslot from file."
    readTimeFromFile()    
    await interaction.response.send_message(update_message)
    
# Command to update the remaining attempts of a user
@tree.command(name="score", description="Set score for stages")
@app_commands.describe(name="The optional argument. If not provided, update member with your discord name")
@app_commands.describe(stage1="The optional argument - number only. If not provided, change nothing")
@app_commands.describe(stage2="The optional argument - number only. If not provided, change nothing")
@app_commands.describe(stage3="The optional argument - number only. If not provided, change nothing")
@app_commands.describe(stage4="The optional argument - number only. If not provided, change nothing")
@app_commands.describe(stage5="The optional argument - number only. If not provided, change nothing")
async def stage_command(interaction, name: Optional[str] = None, stage1: Optional[str] = None, stage2: Optional[str] = None, \
                        stage3: Optional[str] = None, stage4: Optional[str] = None, stage5: Optional[str] = None):
    if name is None:
        name = interaction.user.global_name
        
    error = False

    update_message = interaction.user.global_name + " updated scores for " + name + "."
    
    if stage1 is not None:
        if re.match(r'^-?\d+(?:\.\d+)$', stage1) is None and not stage1.isdigit():
            update_message += "\nIncorrect format. Please enter only number for stage1"
            error = True
    else:
        stage1 = -1
            
    if stage2 is not None:
        if re.match(r'^-?\d+(?:\.\d+)$', stage2) is None and not stage2.isdigit():
            update_message += "\nIncorrect format. Please enter only number for stage2"
            error = True            
    else:
        stage2 = -1            
            
    if stage3 is not None:
        if re.match(r'^-?\d+(?:\.\d+)$', stage3) is None and not stage3.isdigit():
            update_message += "\nIncorrect format. Please enter only number for stage3"
            error = True            
    else:
        stage3 = -1            
            
    if stage4 is not None:
        if re.match(r'^-?\d+(?:\.\d+)$', stage4) is None and not stage4.isdigit():
            update_message += "\nIncorrect format. Please enter only number for stage4"
            error = True            
    else:
        stage4 = -1            
            
    if stage5 is not None:
        if re.match(r'^-?\d+(?:\.\d+)$', stage5) is None and not stage5.isdigit():
            update_message += "\nIncorrect format. Please enter only number for stage5"
            error = True            
    else:
        stage5 = -1            

    if error == False:
        if update_stages(name.lower(), float(stage1), float(stage2), float(stage3), float(stage4), float(stage5)) == False:
            update_message = "\nERROR: '" + name + "' not found"
        else:
            update_message += composeScoreMessage(name.lower())
            
    global logFile        
    logFile.write("\n" + update_message)
    
    await interaction.response.send_message(update_message)

# Command to update the remaining attempts of a user
@tree.command(name="reseta", description="Reset score for all members")
async def reseta_command(interaction):
    update_message = interaction.user.global_name + " reset scores for everyone."
    reset_all_member_stages();
   
    await interaction.response.send_message(update_message)

# Command to update the remaining attempts of a user
@tree.command(name="reset", description="Reset score for stages")
@app_commands.describe(name="Reset stage scores for a member")
async def reset_command(interaction, name: str):        
    error = False

    update_message = interaction.user.global_name + " reset scores for '" + name + "'."

    if error == False:
        if update_stages(name.lower(), 0, 0, 0, 0, 0) == False:
            update_message = "\nERROR: '" + name + "' not found"
        else:
            update_message += composeScoreMessage(name.lower())
            
    global logFile        
    logFile.write("\n" + update_message)
    
    await interaction.response.send_message(update_message)
    
# Command to show everyone from the database
@tree.command(name="show", description="Show the number of attempts left")#,             guild=discord.Object(id=GUILD_ID))
@app_commands.describe(all="The optional argument. If not provided, display only members with attempts left.")
async def show_command(interaction, all: Optional[bool] = False):
    resp_message = composeRemainingMessage(all)
    channel = client.get_channel(interaction.channel_id)   
    
    i = 0
    for msg in resp_message:
        if i == 0:
            await interaction.response.send_message(msg)
            i += 1
        elif msg != "":
            await channel.send(msg)   
            
# Command to show everyone from the database
@tree.command(name="shows", description="Show members with the score matching filter")#,             guild=discord.Object(id=GUILD_ID))
@app_commands.describe(min_score="Optional. Display members with score >= this score. If not provided, assume 0")
@app_commands.describe(max_score="Optional. Display members with score <= this score. If not provided, assume 100")
@app_commands.describe(avail="Optional. True if they're pingable at the time of usage. If not provided, will display all")
@app_commands.describe(stage="Display the stage of members that still have any attempt left")
@app_commands.choices(stage=[
    app_commands.Choice(name='stage 1', value=1),
    app_commands.Choice(name='stage 2', value=2),
    app_commands.Choice(name='stage 3', value=3),
    app_commands.Choice(name='stage 4', value=4),
    app_commands.Choice(name='stage 5', value=5),    
])
async def show_stage_command(interaction, stage: app_commands.Choice[int], min_score: Optional[int] = 0, max_score: Optional[int] = 100, avail: Optional[bool] = False):
    resp_message = composeStageMessage(stage.value, 0, min_score, max_score, avail)
    await interaction.response.send_message(resp_message)

# Command to add a guild member to the database
@tree.command(name="add", description="Add a guild member to the database")#,     guild=discord.Object(id=GUILD_ID))
async def add_command(interaction, name: str):
    resp_message = interaction.user.global_name + " added " + name + " to the battle ranking"
    if (add_member(name.lower()) == False):
        resp_message = name + " is already in the database"
    if resp_message != None:        
        logFile.write("\n" + resp_message)
    await interaction.response.send_message(resp_message)

# Command to remove a guild member from the database
@tree.command(name="remove", description="Remove a guild member from the database")#,
#     guild=discord.Object(id=GUILD_ID))
async def remove_command(interaction, name: str):
    global logFile    
    resp_message = interaction.user.global_name + " removed " + name + " from the battle ranking"
    delete_member(name.lower())
    if resp_message != None:    
        logFile.write("\n" + resp_message)        
    await interaction.response.send_message(resp_message)


# Command to show everyone from the database
@tree.command(name="showt", description="Show timeslots for the next 5 hours")
async def showt_command(interaction):
    resp_message = composeTimeMessage()
    await interaction.response.send_message(resp_message)

# Command to assign stage assignment and save to the database
@tree.command(name="astage", description="Set stage assignment for the guild battle")
@app_commands.describe(name="Assign a stage to a member. If not provided, use your discord name.")
@app_commands.describe(stage="Assign a stage to a member. If not provided, user is not assigned to any stage.")
@app_commands.choices(stage=[
    app_commands.Choice(name='none', value=0),
    app_commands.Choice(name='stage 1', value=1),
    app_commands.Choice(name='stage 2', value=2),
    app_commands.Choice(name='stage 3', value=3),
    app_commands.Choice(name='stage 4', value=4),
    app_commands.Choice(name='stage 5', value=5),    
])
async def astage_command(interaction, name: Optional[str] = None, stage: app_commands.Choice[int] = 0):
    if name is None:
        name = interaction.user.global_name
  
    if stage.value > 5 or stage.value < 0:
        update_message = "\nCommand failed. Invalid stage."
        await interaction.response.send_message(update_message)
        return

    if stage.value != 0:
        update_message = interaction.user.global_name + " assigned stage " + str(stage.value) + " to '" + name + "'."
    else:
        update_message = interaction.user.global_name + " removed stage assignment for '" + name + "'."
    
    if (update_assign(name.lower(), stage.value) == False):
        update_message = "\nERROR: '" + name + "' not found"
        
    logFile.write("\n" + update_message)
    
    await interaction.response.send_message(update_message)


# Command to assign stage assignment and save to the database
@tree.command(name="alink", description="Set stage assignment for the guild battle")#,
#     guild=discord.Object(id=GUILD_ID))
async def alink_command(interaction, link: str):   
    if "discord.gg/" not in link and "discord.com/" not in link:
        await interaction.response.send_message("\nWrong format. Not a discord link.")
    else:
        global assignmentLink
        global logFile
        assignmentLink = link
        resp_message = interaction.user.global_name + " set " + assignmentLink + " as stage assignment"
        # write to the database - need to redesign the database a bit
        if resp_message != None:    
            logFile.write("\n" + resp_message)        
        await interaction.response.send_message(resp_message)
    
# Command to show stage assignment
@tree.command(name="showa", description="Show stage assignment for the guild battle")#,
#     guild=discord.Object(id=GUILD_ID))
async def showa_command(interaction):
    resp_message = " Stage assignment: "
# discord message format EX:  https://discord.com/channels/1273976720382234675/1288668100631330828/1289912810998071387
#                             https://discordapp.com/channels/guild_id/channel_id/message_id
    global assignmentLink       
  
    if (assignmentLink == None):
        resp_message = "No stage assignment found."
    else:
#        print("link " + assignmentLink)
        link = assignmentLink.split('/')
        server_id = int(link[4])
        channel_id = int(link[5])
        msg_id = int(link[6])
        server = client.get_guild(server_id)
        channel = server.get_channel(channel_id)
        message = await channel.fetch_message(msg_id)
        resp_message = message.content
        
        #print(str(server_id) + " " + str(channel_id) + " " + str(msg_id))        
        #print(message.content)
      
    await interaction.response.send_message(resp_message)


# Task event that run at eventTime - Reset all attempts
@tasks.loop(time=eventTime)
async def reset_once_a_day():
    await writeDataToDatabase() # daily writing data to the database
    
    global logFile
    logFile.write("\n\nData before reset:")
    writeData(logFile)    
    logFile.close() # Close old log file and make a new log file    
    
    logFile = open("log_" + str(datetime.now().strftime('%Y-%m-%d')) + ".txt", "a", encoding="utf-8")  
        
    reset_attempts()    
    message = "\nAll remaining attempts were reset at (PST) " + str(datetime.now())
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
    logFile = open("log_" + str(datetime.now().strftime('%Y-%m-%d')) + ".txt", "a", encoding="utf-8")
    
    # Read keys from the database
    readDataFromDatabase()
    
    # Read time from file
    readTimeFromFile()
    
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
        return db[name]["attempts"]
    else:
        return -1

# Composes time message
def composeTimeMessage():
    now = datetime.now(timezone.utc)
    hour = now.hour # get current hour
    resp_message = "Current time (UTC): " + str(now.hour) + ":" + str(now.minute) +":" + str(now.second) + "."
               
    # Print all the keys from the database
    keys = db.keys() 
  
    t = PrettyTable(['Name', 'Now', 'Now+1', 'Now+2', 'Now+3', 'Now+4'])
   
    for key in sorted(keys):
        currHour = hour
        freeTime = []

        for i in range(5):
            if currHour < 0 or currHour > 23:
                currHour = 0
            freeTime.append(getTimeAvailable(key, currHour))
            currHour += 1
        
        if db[key]["attempts"]:
            t.add_row([key, freeTime[0], freeTime[1], freeTime[2], freeTime[3], freeTime[4]])

        freeTime.clear()

    resp_message += f"```{t}```"    
    
    return resp_message

# Composes stage message, sorted
def composeStageMessage(stage, attempt, minS, maxS, avail):
    now = datetime.now(timezone.utc)
    hour = now.hour # get current hour
    resp_message = "Current time (UTC): " + str(now.hour) + ":" + str(now.minute) +":" + str(now.second) + ". \nMin: " + str(minS) + " max: " + str(maxS)
#    count = 0
                
    # Print all the keys from the database
    keys = db.keys()   
    
    t = PrettyTable(['Name', '#', 'Stg', '%', 'Now', 'Next'])

    if stage == 1:
        sorted_dict = dict(sorted(db.items(), key=lambda item: item[1]['stage 1'], reverse=True))
    elif stage == 2:
        sorted_dict = dict(sorted(db.items(), key=lambda item: item[1]['stage 2'], reverse=True))
    elif stage == 3:
        sorted_dict = dict(sorted(db.items(), key=lambda item: item[1]['stage 3'], reverse=True))
    elif stage == 4:
        sorted_dict = dict(sorted(db.items(), key=lambda item: item[1]['stage 4'], reverse=True))
    elif stage == 5:
        sorted_dict = dict(sorted(db.items(), key=lambda item: item[1]['stage 5'], reverse=True))

    for key in sorted_dict:
        if stage == 1:
            value = db[key]['stage 1']
            valueS = str(value)
            if db[key]['assign'] == 1:
                valueS = valueS + "*"
        elif stage == 2:
            value = db[key]['stage 2']
            valueS = str(value)            
            if db[key]['assign'] == 2:
                valueS = valueS + "*"
        elif stage == 3:
            value = db[key]['stage 3']
            valueS = str(value)            
            if db[key]['assign'] == 3:
                valueS = valueS + "*"
        elif stage == 4:
            value = db[key]['stage 4']
            valueS = str(value)            
            if db[key]['assign'] == 4:
                valueS = valueS + "*"
        elif stage == 5:
            value = db[key]['stage 5']
            valueS = str(value)            
            if db[key]['assign'] == 5:
                valueS = valueS + "*"
        else:
            break
        
        freetime = getTimeAvailable(key, hour)
        nextFreeTime = getTimeAvailable(key, hour+1)
        display = True
        if avail == True:
            if freetime != 'Y' and freetime != 'M':
                display = False
        
        if db[key]["attempts"] > attempt and value >= minS and value <= maxS and display:
#            resp_message += "\n"
#            newstr = key + ": " + str(db[key]["attempts"])
#            resp_message += newstr
#            newstr = "\tStg " + str(stage) + ": " + str(value) + "%"
#            resp_message += newstr
            t.add_row([key, db[key]["attempts"], str(stage), valueS, freetime, nextFreeTime])#'''getTimeAvailable(key, hour+1)'''0])
#            count += 1
#            if count > 15:
#                resp_message += "\nExceeding discord length limit. Filter to see more members."
#                break

    resp_message += f"```{t}```"
    
#    print("\nLength: ")
#    print(len(resp_message))
    
    return resp_message

# Composes the message to be sent to the channel with all the remaining attempts
# of the key-value pairs in the database
def composeRemainingMessage(allMembers):
    final_message = []
    resp_message = "Remaining attempts for today:"
    # Print all the keys from the database
    keys = db.keys()    
 
#    print(keys)
#    print("\n")
#    t = PrettyTable(['name', 'attempts', 'stage 1', 'stage 2', 'stage 3', 'stage 4', 'stage 5'])
#    for key in sorted(keys):
#        if db[key]["attempts"] > 0 or allMembers == True:
#            t.add_row([key, db[key]["attempts"], db[key]["stage 1"], db[key]["stage 2"], db[key]["stage 3"], db[key]["stage 4"], db[key]["stage 5"]])
#    resp_message = f"```{t}```"            
#    print(t)
           
#    for key in sorted(keys):
#        if db[key]["attempts"] > 0 or allMembers == True:
#            resp_message += key + ": " + str(db[key]["attempts"]) + " [Stg 1: " + str(db[key]["stage 1"]) + "%, Stg 2:" + str(db[key]["stage 2"]) + \
#                            "%, Stg 3: " + str(db[key]["stage 3"]) + "%, Stg 4: " + str(db[key]["stage 4"]) + "%, Stg 5: " + str(db[key]["stage 5"])
#            resp_message += "%]\n"
    
    count = 0
    for key in sorted(keys):
        if db[key]["attempts"] > 0 or allMembers == True:
#            resp_message += "\n" + key + ": " + str(db[key]["attempts"])
#            resp_message += f"{"\n        Stg 1: " + str(db[key]["stage 1"]) + "%":>40}"
#            resp_message += f"{"Stg 2: " + str(db[key]["stage 2"]) + "%":<40}"
#            resp_message += f"{"\n        Stg 3: " + str(db[key]["stage 3"]) + "%":>40}"            
#            resp_message += f"{"Stg 4: " + str(db[key]["stage 4"]) + "%":<40}"
#            resp_message += "\n        Stg 5: " + str(db[key]["stage 5"]) + "%"
            resp_message += "\n**" + key + "**: " + str(db[key]["attempts"])
            resp_message += "\n     Stg 1: " + str(db[key]["stage 1"]) + "%"
            resp_message += "\tStg 2: " + str(db[key]["stage 2"]) + "%"
            resp_message += "\tStg 3: " + str(db[key]["stage 3"]) + "%"
            resp_message += "\n     Stg 4: " + str(db[key]["stage 4"]) + "%"
            resp_message += "\tStg 5: " + str(db[key]["stage 5"]) + "%"
            count += 1
            if count >= 15:   # more than 15 members
                final_message.append(resp_message)
                resp_message = ""
                count = 0
                
    final_message.append(resp_message)        
    return final_message

def composeScoreMessage(name):
    resp_message = "\nNew scores for " + name + ":"
    if name in db.keys():
        resp_message += "\n     Stg 1: " + str(db[name]["stage 1"]) + "%"
        resp_message += "\tStg 2: " + str(db[name]["stage 2"]) + "%"
        resp_message += "\tStg 3: " + str(db[name]["stage 3"]) + "%"
        resp_message += "\n     Stg 4: " + str(db[name]["stage 4"]) + "%"
        resp_message += "\tStg 5: " + str(db[name]["stage 5"]) + "%"
    return resp_message
    
    
# Reset all remaining attempts to MAX_ATTEMPTS
def reset_attempts():
    keys = db.keys()
    for key in keys:
        db[key]["attempts"] = MAX_ATTEMPTS

# Update the remaining attempts of a member
def update_attempts(name, attempts):
  if name in db.keys():
    db[name]["attempts"] = attempts
    return True
  else:
    return False

# Reset scores for all members
def reset_all_member_stages():
    keys = db.keys()
    for name in keys:
        db[name]["stage 1"] = 0
        db[name]["stage 2"] = 0        
        db[name]["stage 3"] = 0
        db[name]["stage 4"] = 0
        db[name]["stage 5"] = 0
        db[name]["assign"] = 0

# Update the stages of a member
def update_stages(name, stage1, stage2, stage3, stage4, stage5):
  if name in db.keys():
    if stage1 >= 100:
        db[name]["stage 1"] = 100
    elif stage1 >= 0:
        db[name]["stage 1"] = stage1

    if stage2 >= 100:
        db[name]["stage 2"] = 100        
    elif stage2 >= 0:        
        db[name]["stage 2"] = stage2
        
    if stage3 >= 100:
        db[name]["stage 3"] = 100
    elif stage3 >= 0:    
        db[name]["stage 3"] = stage3
        
    if stage4 >= 100:
        db[name]["stage 4"] = 100
    elif stage4 >= 0:    
        db[name]["stage 4"] = stage4
        
    if stage5 >= 100:
        db[name]["stage 5"] = 100
    elif stage5 >= 0:    
        db[name]["stage 5"] = stage5
    return True
  else:
    return False  

def update_assign(name, value):
  if name in db.keys():
      db[name]["assign"] = value
      return True
  else:
      return False

# Add a member to the database
def add_member(name):
    if name not in db:
        db[name] = {}
        db[name]["attempts"] = MAX_ATTEMPTS
        db[name]["stage 1"] = 0
        db[name]["stage 2"] = 0
        db[name]["stage 3"] = 0
        db[name]["stage 4"] = 0
        db[name]["stage 5"] = 0        
        db[name]["assign"] = 0
        return True
    else:
        return False

# Remove a member from the database
def delete_member(name):
    if name in db:
        del db[name]
    if name not in db:
       logFile.write("\n" + name + " deleted successfully.")

def writeData(f): 
    global assignmentLink    
    f.write(assignmentLink + "\n")
    keys = db.keys()
    
    for key in keys:
        data = key + "," + str(db[key]["attempts"]) + "," + str(db[key]["stage 1"]) + "," + str(db[key]["stage 2"]) + "," + str(db[key]["stage 3"]) + "," + str(db[key]["stage 4"]) + "," + str(db[key]["stage 5"]) + "," + str(db[key]["assign"]) + "\n"
        f.write(data)

def readDataFromDatabase():
    with open('data.txt') as f:
        lines = f.readlines()
        global assignmentLink
        assignmentLink = lines[0]
#        print("assignment from: " + assignmentLink)
#        print("Data:\n")
        for line in lines[2:]:            
            if line: # if line is not empty
                data = line.split(',')
#                print(line)                    
#                print(data)                
#                print(str(data[1]))
                db[data[0]]={}                
                db[data[0]]["attempts"] = int(data[1])
                db[data[0]]["stage 1"] = float(data[2])
                db[data[0]]["stage 2"] = float(data[3])
                db[data[0]]["stage 3"] = float(data[4])
                db[data[0]]["stage 4"] = float(data[5])
                db[data[0]]["stage 5"] = float(data[6])
                db[data[0]]["assign"] = int(data[7])
#        print(db)
    f.close()
    
async def writeDataToDatabase():
    f = open("data.txt", "w", encoding="utf-8")
    writeData(f)
    f.close()  
    
def getTimeAvailable(key, hour):
    if key not in timedb:
        print(key + "is not in timedb")
        return ''
    
    if hour < 0 or hour > 23:
        hour = 0  
    
    match hour:
        case 0:
#            if timedb[key]["0"] == 'Y' or timedb[key]["0"] == 'M':
#                return True
             return timedb[key]["0"]          
        case 1:
#            if timedb[key]["1"] == 'Y' or timedb[key]["1"] == 'M':
             return timedb[key]["1"]          
        case 2:
#            if timedb[key]["2"] == 'Y' or timedb[key]["2"] == 'M':
             return timedb[key]["2"]          
        case 3:
#            if timedb[key]["3"] == 'Y' or timedb[key]["3"] == 'M':
             return timedb[key]["3"]          
        case 4:
 #           if timedb[key]["4"] == 'Y' or timedb[key]["4"] == 'M':
             return timedb[key]["4"]          
        case 5:
#            if timedb[key]["5"] == 'Y' or timedb[key]["5"] == 'M':
             return timedb[key]["5"]          
        case 6:
#            if timedb[key]["6"] == 'Y' or timedb[key]["6"] == 'M':
             return timedb[key]["6"]          
        case 7:
#            if timedb[key]["7"] == 'Y' or timedb[key]["7"] == 'M':
             return timedb[key]["7"]          
        case 8:
#            if timedb[key]["8"] == 'Y' or timedb[key]["8"] == 'M':
             return timedb[key]["8"]                       
        case 9:
#            if timedb[key]["9"] == 'Y' or timedb[key]["9"] == 'M':
             return timedb[key]["9"]                       
        case 10:
 #           if timedb[key]["10"] == 'Y' or timedb[key]["10"] == 'M':
             return timedb[key]["10"]                       
        case 11:
 #           if timedb[key]["11"] == 'Y' or timedb[key]["11"] == 'M':
             return timedb[key]["11"]           
        case 12:
#            if timedb[key]["12"] == 'Y' or timedb[key]["12"] == 'M':
             return timedb[key]["12"]                       
        case 13:
#            if timedb[key]["13"] == 'Y' or timedb[key]["13"] == 'M':
             return timedb[key]["13"]                       
        case 14:
#            if timedb[key]["14"] == 'Y' or timedb[key]["14"] == 'M':
             return timedb[key]["14"]                       
        case 15:
#            if timedb[key]["15"] == 'Y' or timedb[key]["15"] == 'M':
             return timedb[key]["15"]                       
        case 16:
#            if timedb[key]["16"] == 'Y' or timedb[key]["16"] == 'M':
             return timedb[key]["16"]                       
        case 17:
#            if timedb[key]["17"] == 'Y' or timedb[key]["17"] == 'M':
             return timedb[key]["17"]                       
        case 18:
#            if timedb[key]["18"] == 'Y' or timedb[key]["18"] == 'M':
             return timedb[key]["18"]                    
        case 19:
#            if timedb[key]["19"] == 'Y' or timedb[key]["19"] == 'M':
             return timedb[key]["19"]                       
        case 20:
#            if timedb[key]["20"] == 'Y' or timedb[key]["20"] == 'M':
             return timedb[key]["20"]                       
        case 21:
 #           if timedb[key]["21"] == 'Y' or timedb[key]["21"] == 'M':
             return timedb[key]["21"]                       
        case 22:
#            if timedb[key]["22"] == 'Y' or timedb[key]["22"] == 'M':
             return timedb[key]["22"]                       
        case 23:                
#            if timedb[key]["23"] == 'Y' or timedb[key]["23"] == 'M':
             return timedb[key]["23"]               
        case _:  # Default case - shouldn't hit this...
            return ''

def readTimeFromFile():
    with open('time.csv') as f:
        lines = f.readlines()
        for line in lines[1:]:          
            if line: # if line is not empty
                data = line.split(',')
                timedb[data[0]]={}                
                timedb[data[0]]["zone"] = data[1]
                timedb[data[0]]["0"] = data[2]
                timedb[data[0]]["1"] = data[3]
                timedb[data[0]]["2"] = data[4]
                timedb[data[0]]["3"] = data[5]
                timedb[data[0]]["4"] = data[6]
                timedb[data[0]]["5"] = data[7]
                timedb[data[0]]["6"] = data[8]
                timedb[data[0]]["7"] = data[9]
                timedb[data[0]]["8"] = data[10]
                timedb[data[0]]["9"] = data[11]
                timedb[data[0]]["10"] = data[12]
                timedb[data[0]]["11"] = data[13]
                timedb[data[0]]["12"] = data[14]
                timedb[data[0]]["13"] = data[15]
                timedb[data[0]]["14"] = data[16]
                timedb[data[0]]["15"] = data[17]
                timedb[data[0]]["16"] = data[18]
                timedb[data[0]]["17"] = data[19]
                timedb[data[0]]["18"] = data[20]
                timedb[data[0]]["19"] = data[21]
                timedb[data[0]]["20"] = data[22]
                timedb[data[0]]["21"] = data[23]
                timedb[data[0]]["22"] = data[24]
                timedb[data[0]]["23"] = data[25].strip()
    f.close()        
    
client.run(token)

        

                