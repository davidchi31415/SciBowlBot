from additional_commands import *
from game import *
import config, discord.utils
from discord.ext import commands
import urllib.request, os, leaderboards

bot = commands.Bot(command_prefix = "p!") #Change this prefix to whatever you like :)
idle_status = discord.Game("Available | p!help for info")
dnd_status = discord.Game("In a game | p!help for info")
team_a = None
team_b = None
game = None
vc = None

@bot.event
async def on_ready():
    appinfo = await bot.application_info()
    bot.procUser = appinfo.owner
    print('Logged on.'.format(bot.user.name, bot.user.id))
    await bot.change_presence(status=discord.Status.online, activity=idle_status)

@bot.command(help="This can only be done under the 'Section for Practice' category of the "
                    "server. Only use it in #start-a-game.", brief="Starts game")
async def play(ctx):
    if ctx.message.channel.guild.id != config.GUILD:
        await ctx.send(":x: Not the right server")
    if ctx.message.channel.category_id != config.CATEGORY_ID and ctx.message.channel.guild.id == config.GUILD:
        await ctx.send(":x: Not the right category to start game")
    else:
        global team_a
        global team_b
        global game
        global vc
        initial_message = ctx.message
        if game is None:
            team_a = Team("A")
            team_b = Team("B")
            game = Game(team_a, team_b, initial_message.channel, bot, ctx.message.author)
            await bot.change_presence(status=discord.Status.dnd, activity=dnd_status)
            await game.play()
            vc = await game.voice_channel.connect()
        else:
            await ctx.send(":x: Already in game")

@bot.command(help="Deletes channels created at start of game but saves data of questions from game to #game-log.",
             brief="Ends game")
async def end(ctx):
    global game
    global team_a
    global team_b
    global vc
    if game is not None:
        await game.end_game()
        if len(game.questions) != 0:
            await game.save_data()
        await bot.change_presence(status=discord.Status.online, activity=idle_status)
        game = None
        team_a = None
        team_b = None
        vc = None
    else:
        await ctx.send(":x: Not in a game")

@bot.event
async def on_reaction_add(reaction, user):
    global game
    global team_a
    global team_b
    global vc
    if user.id != bot.user.id and len(game.current_proctor_button) != 0\
            and user.id == game.proctor.id:
        for button in game.current_proctor_button:
            if reaction.message.id == button.message.id:
                if button.get_type() == "ask question":
                    await game.questions[-1].ask(game)
                if button.get_type() == "start timer":
                    game.current_proctor_button.remove(button)
                    await game.questions[-1].start(game)
                if button.get_type() == "ask to skip":
                    game.current_proctor_button = []
                    game.current_button = None
                    await game.text_channel.send("**Question #{} has been skipped.**".format(game.questions[-1].number))
                    await game.questions[-1].skip(game)
                    await game.ask_question_type()
                if button.get_type() == "ask to verify":
                    if reaction.emoji == "✅":
                        game.current_proctor_button = []
                        await game.questions[-1].player_correct(game)
                        await game.ask_question_type()
                    else:
                        if not game.questions[-1].timer._stop:
                            game.questions[-1].timer.stop()
                        await game.questions[-1].player_incorrect(game)
                if button.get_type() == "ask to resume":
                    await game.questions[-1].ask(game)
                if button.get_type() == "get type":
                    if reaction.emoji == "🥏":
                        game.current_proctor_button = []
                        await game.ask_question_subject("Toss-up")
                    if reaction.emoji == "🏆":
                        game.current_proctor_button = []
                        await game.ask_question_subject("Bonus")







    if user.id != bot.user.id and game.current_button is not None:
        if reaction.message.id == game.current_button.message.id \
                and reaction.message.channel.id == game.text_channel.id:

            buzzer = None
            for player in team_a.players:
                 if player.id == user.id:
                    buzzer = player
            for another_player in team_b.players:
                if another_player.id == user.id:
                    buzzer = another_player
            if buzzer is not None:
                if not buzzer.get_team().has_buzzed():
                    game.current_button = None
                    game.current_proctor_button = []
                    vc.play(discord.FFmpegPCMAudio("buzzer.mp3"))
                    await game.questions[-1].detect_buzz(buzzer, game)
                    await game.ask_verify()
                else:
                    em = discord.Embed(title="Cannot buzz twice", description="{}, Team {} can't buzz again.".format(
                        buzzer.get_name(), buzzer.get_team().name
                      ), color=0xff0000)
                    await game.text_channel.send(embed=em)

@bot.command(help="Note bulk delete does not work on messages older than 14 days.",
             brief="Deletes up to 100 messages.")
async def msgdel(ctx, number):
    await delete(ctx.message.channel, number)

@bot.command(help="Deletes all game log files from local directory (server).", brief="Deletes storage files.")
async def clear_files(ctx):
    await leaderboards.clear_log(ctx)

@bot.command(help="Deletes all leaderboard data.", brief="ONLY TEACHER CAN DO THIS.")
async def clear_data(ctx):
    if ctx.message.channel.guild.get_role(config.TEACHER) in ctx.message.author.roles:
        if os.path.isfile("data.csv"):
            await ctx.send(":question: Are you sure? (**Yes**/**No**) *10 seconds to respond*")
            def check(m):
                return m.author == ctx.message.author and m.content.upper()=="YES"
            clarify = await bot.wait_for("message", check=check, timeout=10)
            if clarify:
                os.remove("data.csv")
                await ctx.send(":white_check_mark: `data.csv` deleted.")
        else:
            await ctx.send(":x: No data to remove")
    else:
        await ctx.send(":x: Insufficient permissions")

@bot.command(help="Displays leaderboard.", brief="Compare.")
async def show_leaderboard(ctx):
    global game
    in_a_game = False
    if game is not None:
        in_a_game = True
    await leaderboards.leaderboard_display(ctx, in_a_game)

@bot.event
async def on_member_join(member):
    await leaderboards.append_to_file(member)



bot.run(config.TOKEN)


