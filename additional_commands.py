import discord, random

async def send_message(channel, message, sendTyping = True, embed=None):
    if sendTyping:
        await channel.trigger_typing()
        await channel.send(message, embed=embed)
    else:
        await channel.send(message, embed=embed)

async def send_embed(channel, title, description, color, fields, values):
    embedVar = discord.Embed(title=title, description=description, color=color)
    for i in range(len(fields)):
        embedVar.add_field(name=fields[i], value=values[i])
    await channel.send(embed=embedVar)

async def delete(channel, number):
    try:
        amount = int(number)
        if amount > 100:
            await send_message(channel, ":x::speech_balloon: Number of messages to be deleted cannot exceed `100`.")
        else:
            messages = await channel.history(limit=amount).flatten()
            await channel.delete_messages(messages)
            await send_message(channel, ":white_check_mark: Deleted `{}` messages.".format(len(messages)))
    except TypeError:
        random_number = random.randint(0, 3)
        if random_number == 0:
            await send_message(channel, ":x::speech_balloon: What the heck did you just type? :D")
        if random_number == 1:
            await send_message(channel, ":x::speech_balloon: Bruh quit playin and just send a real number.")
        if random_number == 2:
            await send_message(channel, ":x::speech_balloon: Are you Kunaal or something?")
        if random_number == 3:
            await send_message(channel, ":x::speech_balloon: Yeah uhh I don't understand your request.")
    except ValueError:
        random_number = random.randint(0, 3)
        if random_number == 0:
            await send_message(channel, ":x::speech_balloon: What the heck did you just type? :D")
        if random_number == 1:
            await send_message(channel, ":x::speech_balloon: Bruh quit playin and just send a real number.")
        if random_number == 2:
            await send_message(channel, ":x::speech_balloon: Are you Kunaal or something?")
        if random_number == 3:
            await send_message(channel, ":x::speech_balloon: Yeah uhh I don't understand your request.")

