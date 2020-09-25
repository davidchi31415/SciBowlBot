import asyncio, csv, config, datetime, os, leaderboards
from additional_commands import *


class Question:
    def __init__(self, number, subject, timer, channel):
        self.type = "Toss-up"
        self.subject = subject
        self.number = number
        self.buzzer_list = []
        self.correct = None
        self.incorrect = []
        self.timer = timer
        self.channel = channel

    # minor functions (get called during major functions)
    def typeset(self, type):
        self.type = type

    def reset_timer(self):
        self.timer.reset()

    def start_timer(self):
        self.timer.start()

    async def detect_buzz(self, player, game):
        if not player.get_team().has_buzzed():
            self.buzzer_list.append(player)
            if player.team_status == "Captain":
                await send_embed(game.proctor_channel, "Buzz", "Player {} | {} {}".format(player.get_name(),
                                                                                          player.get_team().name,
                                                                                          player.team_status),
                                 0xffff00, [], [])
            else:
                await send_embed(game.proctor_channel, "Buzz", "Player {} | {}".format(player.get_name()
                                                                                       , player.team_status),
                                 0xffff00, [], [])
            if self.type == "Bonus":
                await player.buzz(self, bonus=True)  # calls for question.display_buzz()
            else:
                await player.buzz(self)
            if not self.timer._stop:
                await self.timer.stop()

        player.get_team().has_buzzed_already = True

    async def player_correct(self, game):
        # gets called by proctor
        self.correct = self.buzzer_list[-1]
        if game.questions[-1].type == "Bonus":
            for player in self.buzzer_list[-1].get_team().players:
                player.correct(bonus=True)  # change player status to correct (temporary)
        else:
            self.buzzer_list[-1].correct()
        await self.end(game)

    async def player_incorrect(self, game):
        self.incorrect.append(self.buzzer_list[-1])
        if self.type == "Bonus":
            self.buzzer_list[-1].incorrect(bonus=True)
        else:
            self.buzzer_list[-1].incorrect()
        em = discord.Embed(title="Incorrect Answer", description="{} | Team {}: You answer was incorrect".format(
            self.buzzer_list[-1].get_name(), self.buzzer_list[-1].get_team().name
        ), color=0xff0000)
        await game.text_channel.send(embed=em)
        await game.ask_resume()

    def adjust_score(self, bonus):
        for player in self.buzzer_list:
            player.get_team().update_stats(bonus)  # team stats update

    async def display_question(self, game):
        embedVar = discord.Embed(title="Question #{}:".format(self.number), color=0xffffff)
        embedVar.add_field(name="Type", value=self.type)
        embedVar.add_field(name="Subject", value=self.subject)
        message = await self.channel.send("Click the red circle to buzz.", embed=embedVar)
        await message.add_reaction("🔴")
        game.current_button = Button(message, "buzzer")
        await send_embed(game.proctor_channel, "Game Control", "Button key", 0xffff00,
                         ["Skip Question", "Start Timer"], ["⏩", "🕰️"])
        game.current_proctor_button = []
        await game.ask_skip()
        await game.ask_start_timer()

    async def display_buzz(self):
        player = self.buzzer_list[-1]
        if player.team_status == "Captain":
            await send_embed(self.channel, "Buzz", "Player {} | {} {}".format(player.get_name(),
                                                                              player.get_team().name,
                                                                              player.team_status), 0xffff00, [], [])
        else:
            await send_embed(self.channel, "Buzz", "Player {} | {}".format(player.get_name()
                                                                           , player.team_status),
                             0xffff00, [], [])

    async def display_result(self, game):
        if self.correct is not None:
            embedVar = discord.Embed(title="Question #{}:".format(self.number),
                                     description="Results", color=0x00ff00)
            results_list_buzz = "None"
            if len(self.buzzer_list) != 0:
                results_list_buzz = " ".join([buzzer.get_name() for buzzer in self.buzzer_list])
            embedVar.add_field(name="Buzzers", value=results_list_buzz, inline=True)
            if self.correct.team_status != "Captain":
                results_list_correct = self.correct.get_name() + " | " + self.correct.team_status
            else:
                results_list_correct = self.correct.get_name() + " | " + self.correct.get_team().name + " " + \
                                       self.correct.team_status
            embedVar.add_field(name="Correct", value=results_list_correct, inline=True)
            embedVar.add_field(name="Team A", value="Score: {}".format(game.team_a.score))
            embedVar.add_field(name="Team B", value="Score: {}".format(game.team_b.score))
            await self.channel.send(embed=embedVar)
        else:
            embedVar = discord.Embed(title="Question #{}:".format(self.number),
                                     description="Results", color=0xff0000)
            results_list_buzz = "None"
            if len(self.buzzer_list) != 0:
                results_list_buzz = " ".join([buzzer.get_name() for buzzer in self.buzzer_list])
            embedVar.add_field(name="Buzzers", value=results_list_buzz, inline=True)
            results_list_correct = "None"
            embedVar.add_field(name="Correct", value=results_list_correct, inline=True)
            embedVar.add_field(name="Team A", value="Score: {}".format(game.team_a.score))
            embedVar.add_field(name="Team B", value="Score: {}".format(game.team_b.score))
            await self.channel.send(embed=embedVar)

    # major functions (call minor functions to perform some major task
    async def ask(self, game):
        await self.display_question(game)

    async def start(self, game):
        # called when proctor is done asking question
        await self.timer.start(self, game)

    async def skip(self, game):
        bonus = False
        if self.type == "Bonus":
            bonus = True
        if not self.timer._stop:
            await self.timer.stop()
        for player in self.buzzer_list:
            self.adjust_score(bonus)
            player.get_team().update_stats(bonus)

    async def resume(self):
        await self.timer.resume()

    async def end(self, game):
        bonus = False
        if self.type == "Bonus":
            bonus = True
        if not self.timer._stop:
            await self.timer.stop()
        for player in self.buzzer_list:
            self.adjust_score(bonus)
            player.get_team().update_stats(bonus)
        game.current_button = None
        await self.display_result(game)


class Timer:
    def __init__(self, time, channel):
        self.time = time
        self.current_count = time
        self._stop = True
        self.channel = channel

    async def tick(self, question, game):
        while not self._stop:
            if self.current_count >= 1:
                await asyncio.sleep(1)
                self.current_count -= 1
            else:
                self.end_timer()
                await self.display("end-timeout")
                await question.end(game)
                await game.ask_question_type()

    async def start(self, question, game):
        self._stop = False
        await self.display("start")
        await self.tick(question, game)

    async def stop(self):
        self._stop = True
        await self.display("stop")

    async def reset(self):
        self.current_count = self.time
        self._stop = True
        await self.display("reset")

    async def display(self, message):
        dict = {"start": "Timer has started.", "stop": "Timer has been stopped.",
                "reset": "Timer has been reset", "end-timeout": "Time has run out."}
        if message != "end-timeout":
            await send_embed(self.channel, "Timer", dict[message], 0xffffff, ["Time:"],
                             ["{} seconds left".format(self.current_count)])
        if message == "end-timeout":
            await send_embed(self.channel, "Timer", dict[message], 0xff0000, [], [])

    def end_timer(self):
        self._stop = True


class Player:
    def __init__(self, team, name, id, team_status):
        self.team = team  # team object
        self.name = name
        self.id = id
        self.team_status = team_status
        self.status_list = []
        self.accuracy = None
        self.buzz_count = 0
        self.points = 0
        self.bonus_correct_count = 0
        self.correct_count = 0
        self.incorrect_count = 0

    async def buzz(self, question, bonus=False):
        if not bonus:
            self.buzz_count += 1
        self.status_list.append("buzz")
        self.team.buzz()
        await question.display_buzz()

    def unbuzz(self):
        self.status_list.remove("buzz")

    def correct(self, bonus=False):
        self.correct_count += 1
        if bonus:
            self.bonus_correct_count += 1
        self.status_list.append("correct")

    def incorrect(self, bonus=False):
        if not bonus:
            self.incorrect_count += 1
        self.status_list.append("incorrect")

    def un_correct(self):
        self.status_list.remove("correct")

    def un_incorrect(self):
        self.status_list.remove("incorrect")

    def is_correct(self):
        # for team update check
        if "correct" in self.status_list:
            return True
        return False

    def is_buzz(self):
        # for team update check
        if "buzz" in self.status_list:
            return True
        return False

    def adjust_score(self):
        if self.buzz_count != 0 and self.correct_count != self.bonus_correct_count:
            self.accuracy = (self.correct_count - self.bonus_correct_count) / self.buzz_count * 100
        self.points = (self.correct_count - self.bonus_correct_count) + 2.5 * self.bonus_correct_count

    def update_stats(self):
        self.adjust_score()
        if "buzz" in self.status_list:
            self.unbuzz()
        if "correct" in self.status_list:
            self.un_correct()
        if "incorrect" in self.status_list:
            self.un_incorrect()

    def get_team(self):
        return self.team

    def get_name(self):
        return self.name


class Team:
    def __init__(self, name):
        self.name = name
        self.players = []
        self.captain = None
        self.accuracy = None
        self.score = 0
        self.correct_count = 0
        self.bonus_correct_count = 0
        self.buzz_count = 0
        self.has_buzzed_already = False  # when true, team cannot answer during a question (prevents double buzzes)

    def add(self, player):
        self.players.append(player)
        if player.team_status == "Captain":
            self.captain = player

    def remove(self, player):
        self.players.remove(player)

    def buzz(self):
        self.has_buzzed_already = True

    def adjust_score(self):
        if self.buzz_count != 0:
            self.accuracy = self.correct_count / self.buzz_count * 100
        self.score = 4 * self.correct_count + 10 * self.bonus_correct_count

    def has_buzzed(self):
        if self.has_buzzed_already:
            return True

    def reset_buzz(self):
        self.has_buzzed_already = False

    def update_stats(self, bonus=False):
        add = False
        for player in self.players:
            if player.is_buzz():
                if not bonus:
                    self.buzz_count += 1
                if player.is_correct() and not bonus:
                    self.correct_count += 1
                if player.is_correct() and bonus:
                    add = True
            player.update_stats()
        if add:
            self.bonus_correct_count += 1
        self.has_buzzed_already = False
        self.adjust_score()

    def find_player(self, id):
        for player in self.players:
            if player.id == id:
                return player


class Button:
    def __init__(self, message, type):
        self.message = message
        self.type = type

    def get_type(self):
        return self.type


class Game:
    def __init__(self, team_a, team_b, channel, bot, proctor):
        self.team_a = team_a
        self.team_b = team_b
        self.channel = channel
        self.questions = []
        self.current_proctor_button = []
        self.current_button = None
        self.bot = bot
        self.proctor = proctor
        self.guild = bot.get_guild(config.GUILD)
        self.proctor_role = self.guild.get_role(config.PROCTOR)
        self.a_team_role = self.guild.get_role(config.A_TEAM)
        self.b_team_role = self.guild.get_role(config.B_TEAM)
        self.teacher_role = self.guild.get_role(config.TEACHER)

        self.end = False
        for item in self.guild.by_category():
            if item[0].id == config.CATEGORY_ID:
                self.category = item[0]

    async def create_player_channels(self):
        channel_permissions_text = {
            self.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
        }
        channel_permissions_voice = {
            self.guild.me: discord.PermissionOverwrite(connect=True, mute_members=True, deafen_members=True,
                                                       move_members=True)
        }
        self.text_channel = await self.guild.create_text_channel("competition-channel",
                                                                 overwrites=channel_permissions_text,
                                                                 category=self.category,
                                                                 reason="Answer questions here")
        self.voice_channel = await self.guild.create_voice_channel("Competition Channel",
                                                                   overwrites=channel_permissions_voice,
                                                                   category=self.category)

    async def prompt_proctor(self):
        prompt_embedVar = discord.Embed(title="Would you like to begin Question #{}?".format(len(self.questions)),
                                        color=0xffffff)
        message = await self.proctor_channel.send(embed=prompt_embedVar)
        react_emoji = await message.add_reaction("✅")
        self.current_proctor_button = [Button(message, "ask question")]

    async def ask_skip(self):
        prompt_embedVar = discord.Embed(title="Skip Question", description="Click button if you want to skip this "
                                                                           "question.",
                                        color=0x0000ff)
        message = await self.proctor_channel.send(embed=prompt_embedVar)
        await message.add_reaction("⏩")

        self.current_proctor_button.append(Button(message, "ask to skip"))

    async def ask_verify(self):
        verify = discord.Embed(title="Verify Answer", description="Is {}'s answer correct?".format(
            self.questions[-1].buzzer_list[-1].get_name()
        ))
        message = await self.proctor_channel.send(embed=verify)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        self.current_proctor_button = [Button(message, "ask to verify")]

    async def ask_resume(self):
        if self.team_a.has_buzzed() and self.team_b.has_buzzed():
            await self.questions[-1].end(self)
            await self.ask_question_type()
        else:
            resume = discord.Embed(title="Resume Question", description="Would you like to resume? "
                                                                        "*If you didn't  start timer, "
                                                                        " this won't change anything.* "
                                                                        "Just hit the button.", color=0xffff00)
            message_to_resume = await self.proctor_channel.send(embed=resume)
            await message_to_resume.add_reaction("▶")
            self.current_proctor_button.append(Button(message_to_resume, "ask to resume"))

    async def ask_question_type(self):
        ask_embedVar = discord.Embed(title="Question #{}".format(len(self.questions) + 1),
                                     color=0xffffff)
        ask_embedVar.add_field(name="Type", value="-")
        ask_embedVar.add_field(name="-", value=" - ")
        message = await self.proctor_channel.send(embed=ask_embedVar)

        a = discord.Embed(title="Type", description="What type of question?",
                          color=0xffffff)
        a.add_field(name="Toss-up", value="🥏")
        a.add_field(name="Bonus", value="🏆")
        message = await self.proctor_channel.send(embed=a)

        await message.add_reaction("🥏")
        await message.add_reaction("🏆")

        self.current_proctor_button = [Button(message, "get type")]

    async def ask_question_subject(self, type):

        def new_check(m):
            return m.author.id == self.proctor.id and m.channel.id == self.proctor_channel.id

        b = discord.Embed(title="Subject", description="Please enter the subject:", color=0xffffff)
        await self.proctor_channel.send(embed=b)

        subject = await self.bot.wait_for("message", check=new_check)

        time = 7
        if type == "Bonus":
            time = 20

        new_question = Question(len(self.questions) + 1, subject.content, Timer(time, self.text_channel),
                                self.text_channel)

        new_question.typeset(type)

        self.questions.append(new_question)
        await self.prompt_proctor()

    async def rank(self):
        await self.proctor.add_roles(self.proctor_role)

    async def unrank(self):
        await self.proctor.remove_roles(self.proctor_role, reason="Game has ended.")

    async def unrole(self):
        for player in self.team_a.players:
            member = self.guild.get_member(player.id)
            await member.remove_roles(self.guild.get_role(config.A_TEAM))
        for player in self.team_b.players:
            member = self.guild.get_member(player.id)
            await member.remove_roles(self.guild.get_role(config.B_TEAM))

    async def create_proctor_channel(self):
        guild = self.guild
        overwrites_list = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions
            =False),
            self.proctor_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
        }
        self.proctor_channel = await guild.create_text_channel("game-control",
                                                               overwrites=overwrites_list, category=self.category,
                                                               reason="Game control (proctor)")

    async def ask_start_timer(self):
        ask_start_timer_embed = discord.Embed(title="Start Timer", description="Start timer by clicking button"
                                                                               " when done asking question.",
                                              color=0xffff00)
        message = await self.proctor_channel.send(embed=ask_start_timer_embed)
        await message.add_reaction("🕰️")
        self.current_proctor_button.append(Button(message, "start timer"))

    async def delete_channels(self):
        await self.text_channel.delete(reason="Game ended.")
        await self.voice_channel.delete(reason="Game ended.")
        await self.proctor_channel.delete()

    async def setup(self):
        redo = True
        duplicate = False
        await self.create_proctor_channel()
        await self.rank()
        await self.create_player_channels()

        embedVar = discord.Embed(title="Please select teams", description="Use @{name}. Note: **Do it slowly to avoid "
                                                                          "messing up order.**",
                                 color=0xffffff)
        message = await self.proctor_channel.send(embed=embedVar)
        embedVar_a_captain = discord.Embed(title="Team A Captain:",
                                           color=0xffffff)
        message_a_captain = await self.proctor_channel.send(embed=embedVar_a_captain)

        def check(m):
            return m.author.id != self.bot.user.id and m.channel.id == self.proctor_channel.id

        a_captain = await self.bot.wait_for("message", check=check)
        for user in self.guild.members:
            for member in a_captain.mentions:
                if member.id == user.id:
                    player = Player(self.team_a, user.display_name, user.id, "Captain")
                    self.team_a.add(player)
                    await user.add_roles(self.a_team_role)

        await asyncio.sleep(1)
        embedVar_a_one = discord.Embed(title="Team A 1:",
                                       color=0xffffff)
        while redo:
            message_a_one = await self.proctor_channel.send(embed=embedVar_a_one)

            a_one = await self.bot.wait_for("message", check=check)
            if len(a_one.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in a_one.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_a.players]:
                        player = Player(self.team_a, user.display_name, user.id, "A 1")
                        self.team_a.add(player)
                        await user.add_roles(self.a_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(a_one.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        redo = True
        await asyncio.sleep(1)
        embedVar_a_two = discord.Embed(title="Team A 2:",
                                       color=0xffffff)
        while redo:
            message_a_two = await self.proctor_channel.send(embed=embedVar_a_two)

            a_two = await self.bot.wait_for("message", check=check)
            if len(a_two.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in a_two.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_a.players]:
                        player = Player(self.team_a, user.display_name, user.id, "A 2")
                        self.team_a.add(player)
                        await user.add_roles(self.a_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(a_two.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        redo = True
        await asyncio.sleep(1)
        embedVar_a_three = discord.Embed(title="Team A 3:",
                                         color=0xffffff)
        while redo:
            message_a_three = await self.proctor_channel.send(embed=embedVar_a_three)

            a_three = await self.bot.wait_for("message", check=check)
            if len(a_three.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in a_three.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_a.players]:
                        player = Player(self.team_a, user.display_name, user.id, "A 3")
                        self.team_a.add(player)
                        await user.add_roles(self.a_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(a_three.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        redo = True
        await asyncio.sleep(1)
        embedVar_b_captain = discord.Embed(title="Team B Captain:",
                                           color=0xffffff)
        while redo:
            message_b_captain = await self.proctor_channel.send(embed=embedVar_b_captain)

            b_captain = await self.bot.wait_for("message", check=check)
            if len(b_captain.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in b_captain.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_b.players]:
                        player = Player(self.team_b, user.display_name, user.id, "B Captain")
                        self.team_b.add(player)
                        await user.add_roles(self.b_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(b_captain.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        redo = True
        await asyncio.sleep(1)
        embedVar_b_one = discord.Embed(title="Team B 1:",
                                       color=0xffffff)
        while redo:
            message_b_one = await self.proctor_channel.send(embed=embedVar_b_one)

            b_one = await self.bot.wait_for("message", check=check)
            if len(b_one.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in b_one.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_b.players]:
                        player = Player(self.team_b, user.display_name, user.id, "B 1")
                        self.team_b.add(player)
                        await user.add_roles(self.b_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(b_one.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        redo = True
        await asyncio.sleep(1)
        embedVar_b_two = discord.Embed(title="Team B 2:",
                                       color=0xffffff)
        while redo:
            message_b_two = await self.proctor_channel.send(embed=embedVar_b_two)

            b_two = await self.bot.wait_for("message", check=check)
            if len(b_two.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in b_two.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_b.players]:
                        player = Player(self.team_b, user.display_name, user.id, "B 2")
                        self.team_b.add(player)
                        await user.add_roles(self.b_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(b_two.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        redo = True
        await asyncio.sleep(1)
        embedVar_b_three = discord.Embed(title="Team B 3:",
                                         color=0xffffff)
        while redo:
            message_b_three = await self.proctor_channel.send(embed=embedVar_b_three)

            b_three = await self.bot.wait_for("message", check=check)
            if len(b_three.mentions) == 0:
                redo = False
            for user in self.guild.members:
                for member in b_three.mentions:
                    if member.id == user.id and member.id not in [x.id for x in self.team_b.players]:
                        player = Player(self.team_b, user.display_name, user.id, "B 3")
                        self.team_b.add(player)
                        await user.add_roles(self.b_team_role)
                        redo = False
                    else:
                        duplicate = True
            if len(b_three.mentions) > 0 and duplicate and redo == True:
                await self.proctor_channel.send(":x: No duplicates. Try again.")
                duplicate = False

        await asyncio.sleep(1)
        embedVar_preview = discord.Embed(title="Team A",
                                         color=0xffffff)
        for player in self.team_a.players:
            embedVar_preview.add_field(name=player.team_status, value=player.name)
        first_embed = await self.proctor_channel.send(embed=embedVar_preview)
        first_embed_again = await self.text_channel.send(embed=embedVar_preview)

        new_embedVar_preview = discord.Embed(title="Team B",
                                             color=0xffffff)
        for player in self.team_b.players:
            new_embedVar_preview.add_field(name=player.team_status, value=player.name)
        second_embed = await self.proctor_channel.send(embed=new_embedVar_preview)
        second_embed_again = await self.text_channel.send(embed=new_embedVar_preview)

        await self.ask_question_type()

    async def play(self):
        await self.setup()

    async def save_data(self):

        filename = datetime.datetime.now().strftime("%Y-%m-%d.%H-%M-%S")
        with open("{}.csv".format(filename), "w+") as file:
            data = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            data.writerow(["#", "Type", "Subject", "Correct Player", "Correct Team", "Buzzers"])
            for question in self.questions:
                if question.correct is not None and len(question.buzzer_list) > 0:
                    data.writerow([question.number, question.type, question.subject, question.correct.get_name(),
                                   question.correct.get_team().name, " | ".join([x.get_name() for
                                                                                 x in
                                                                                 question.buzzer_list])])
                if question.correct is None and len(question.buzzer_list) > 0:
                    data.writerow([question.number, question.type, question.subject, "None",
                                   "None", " | ".join([x.get_name() for x in question.buzzer_list])])
                if len(question.buzzer_list) == 0:
                    data.writerow([question.number, question.type, question.subject, "None",
                                   "None", "None"])
            data.writerow([" "])
            data.writerow(["Player", "Team", "Accuracy (Not including bonus)", "Buzz Count (Not including bonus)",
                           "Correct Count (Not including bonus)", "Incorrect Count", "Bonuses Correct",
                           "Points (1 for each toss-up correct, 2.5 for bonus)"])
            for player in self.team_a.players:
                if player.accuracy is not None:
                    data.writerow([player.get_name(), player.get_team().name, player.accuracy, player.buzz_count,
                                   player.correct_count - player.bonus_correct_count,
                                   player.incorrect_count, player.bonus_correct_count,
                                   player.points])
                else:
                    data.writerow([player.get_name(), player.get_team().name, "None", player.buzz_count,
                                   player.correct_count - player.bonus_correct_count,
                                   player.incorrect_count, player.bonus_correct_count,
                                   player.points])
            data.writerow([" "])
            data.writerow(["Player", "Team", "Accuracy (Not including bonus)", "Buzz Count (Not including bonus)",
                           "Correct Count (Not including bonus)", "Incorrect Count", "Bonuses Correct",
                           "Points (1 for each toss-up correct, 2.5 for bonus)"])
            for player in self.team_b.players:
                if player.accuracy is not None:
                    data.writerow([player.get_name(), player.get_team().name, player.accuracy, player.buzz_count,
                                   player.correct_count - player.bonus_correct_count,
                                   player.incorrect_count, player.bonus_correct_count,
                                   player.points])
                else:
                    data.writerow([player.get_name(), player.get_team().name, "None", player.buzz_count,
                                   player.correct_count - player.bonus_correct_count,
                                   player.incorrect_count, player.bonus_correct_count,
                                   player.points])
            file.close()

        if self.teacher_role in self.proctor.roles:

            if not os.path.isfile("data.csv"):
                leaderboards.create_file(self.guild)

            for player in self.team_a.players:
                leaderboards.write_to_file(self.guild, player, player.buzz_count, player.accuracy,
                                           player.correct_count - player.bonus_correct_count, player.incorrect_count,
                                           player.bonus_correct_count, player.points)
            for player in self.team_b.players:
                leaderboards.write_to_file(self.guild, player, player.buzz_count, player.accuracy,
                                           player.correct_count - player.bonus_correct_count, player.incorrect_count,
                                           player.bonus_correct_count, player.points)

        await self.guild.get_channel(config.LOG_CHANNEL).send(
            file=discord.File(open("{}.csv".format(filename), "rb"), "Game file {}.csv".format(filename))
        )

    async def end_game(self):
        self.end = True
        await self.delete_channels()
        await self.unrank()
        await self.unrole()












































