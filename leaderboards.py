import discord, csv, os

def create_file(server):
    with open("data.csv", "w+", encoding='utf-8') as file:
        csvwriter = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(["Player Name", "Player ID", "Accuracy", "Buzz Count",
                            "Correct Count", "Incorrect Count", "Bonuses Correct",
                            "Points"
                            ])
        for member in server.members:
            if not member.bot:
                csvwriter.writerow([member.display_name, "{}".format(member.id), "None", "0",
                                    "0", "0", "0", "0"])

def write_to_file(server, member, buzz_count, accuracy, correct_count, incorrect_count, bonuses_correct, points):
    total_rows = []
    rows_to_change = []
    with open("data.csv", "r+", newline='') as file:
        line_count = 0
        readCSV = csv.reader(file, delimiter=',')
        for row in readCSV:
            for column in row:
                if str(member.id) == column:
                    if points > 0:
                        rows_to_change.append([line_count, row])
            total_rows.append([line_count, row])
            line_count += 1

    change = False
    with open("data.csv", "r+", newline='') as file_again:
        writeCSV = csv.writer(file_again, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in range(len(total_rows)):
            for x in rows_to_change:
                if row == x[0]:
                    change = True
                    if x[1][2] != "None" and accuracy is not None:
                        writeCSV.writerow([x[1][0], x[1][1], "{}".format((float(x[1][2])*float(x[1][3])
                                                                         + float(accuracy)*float(buzz_count))/(float(
                            x[1][3]) + float(buzz_count)
                        )),
                                            "{}".format(int(x[1][3])+int(buzz_count)),
                                           "{}".format(int(x[1][4])+int(correct_count)),
                                           "{}".format(int(x[1][5])+int(incorrect_count)),
                                           "{}".format(int(x[1][6])+int(bonuses_correct)),
                                           "{}".format(float(x[1][7])+float(points))])
                    if x[1][2] != "None" and accuracy is None:
                        writeCSV.writerow([x[1][0], x[1][1], x[1][2],
                                            "{}".format(int(x[1][3])+int(buzz_count)),
                                           "{}".format(int(x[1][4])+int(correct_count)),
                                           "{}".format(int(x[1][5])+int(incorrect_count)),
                                           "{}".format(int(x[1][6])+int(bonuses_correct)),
                                           "{}".format(float(x[1][7])+float(points))])
                    if x[1][2] == "None" and accuracy is None:
                        writeCSV.writerow([x[1][0], x[1][1], x[1][2],
                                            "{}".format(int(x[1][3])+int(buzz_count)),
                                           "{}".format(int(x[1][4])+int(correct_count)),
                                           "{}".format(int(x[1][5])+int(incorrect_count)),
                                           "{}".format(int(x[1][6])+int(bonuses_correct)),
                                           "{}".format(float(x[1][7])+float(points))])
                    if x[1][2] == "None" and accuracy is not None:
                        writeCSV.writerow([x[1][0], x[1][1], "{}".format(float(accuracy)),
                                            "{}".format(int(x[1][3])+int(buzz_count)),
                                           "{}".format(int(x[1][4])+int(correct_count)),
                                           "{}".format(int(x[1][5])+int(incorrect_count)),
                                           "{}".format(int(x[1][6])+int(bonuses_correct)),
                                           "{}".format(float(x[1][7])+float(points))])
            if not change:
                writeCSV.writerow(total_rows[row][1])
            change = False

async def clear_log(e):
    num = 0
    for f in os.listdir("."):
        if f.endswith(".csv") and f != "data.csv":
            os.remove(f)
            num += 1
    await e.send("`{}` files deleted.".format(num))

async def leaderboard_display(e, in_a_game):
    if not in_a_game:
        if os.path.isfile("data.csv"):
            display_list = []
            with open("data.csv", "r") as leaderboard_file:
                readlines = csv.reader(leaderboard_file, delimiter=",")
                for row in readlines:
                    if len(row) > 0:
                        if row[0] != "Player Name":
                            if float(row[-1]) > 0 and row[2] != "None":
                                display_list.append([float(row[-1]), row[0], row[2],
                                                     row[3], row[4], row[5],
                                                     row[6], row[7]])
                await e.send("`Leaderboard:`")
                i=1
                sorted_display = sorted(display_list, key=lambda x:x[0])[::-1]
                for element in sorted_display:
                    await e.send("`{}. Name: {} | Accuracy: {} | Buzz Count: {} | Correct Count: {} | "
                                 "Incorrect Count: {} | Bonuses Correct: {} | Points: {}`".format(
                        i, element[1], element[2], element[3], element[4], element[5], element[6], float(element[7])))
                    i += 1
                await e.send("Points are the only property considered for ranking. *Accuracy does not include bonus questions, which are answered by the team.*")
                await e.send("**Leaderboard is only updated for games where proctor has teacher role.**")
        else:
            await e.send(":x: No data available")
    else:
        await e.send(":x: Cannot do that in a game")

async def append_to_file(member, remove=False):
    if os.path.isfile("data.csv"):
        replace = True
        with open("data.csv", "r") as leaderboard_file:
            readlines = csv.reader(leaderboard_file, delimiter=",")
            for row in readlines:
                if row[1] == str(member.id):
                    replace = False
        if replace:
            with open("data.csv", "a", newline='') as leaderboard_file:
                writelines = csv.writer(leaderboard_file, delimiter=",")
                writelines.writerow([member.display_name, member.id, "None", "0", "0", "0", "0", "0"])











