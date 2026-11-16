import json
import argparse

MAP = ""
ZONES = False
COLORS = False

# terminal color escape codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"

data = []
lines = {}
guesses = []
exclude = []
possible = [] # empty list means every station possible

def get_station(name: str) -> dict:
    return list(filter(lambda x: x["name"] == name, data))[0]

# returns:
#   0 - less
#   1 - equal
#   2 - greater
def zone_info(orig: list[str], target: list[str]) -> int:
    if type(orig) == int: orig = [orig]
    if type(target) == int: target = [target]
    orig = list(filter(int, orig))
    target = list(filter(int, target))
    r = -1
    for o in orig:
        for t in target:
            if o == t: return 1
            elif o < t: r = 0
            elif o > t: r = 2
    return r

# returns:
#   0 - incorrect line
#   1 - contains correct line
#   2 - correct color, incorrect line
def line_info(orig: list[str], target: list[str]) -> int:
    for o in orig:
        if o in target: return 1
    if COLORS:
        orig_cols = list(map(lambda x: lines[x], orig))
        target_cols = list(map(lambda x: lines[x], target))
        for o in orig_cols:
            if o in target_cols: return 2
    return 0

def distances(station: str) -> dict[str, int]:
    visited = [station]
    distances = [[station]]
    r = {station: 0}
    new = True
    while new:
        new = False
        distances.append([])
        for s in distances[-2]:
            #print(get_station(s)["adjacent"])
            for n in get_station(s)["adjacent"]:
                if type(n) == dict: n = n["name"]
                if n not in visited:
                    visited.append(n)
                    distances[-1].append(n)
                    r[n] = len(distances)-1
                    new = True
    return r

def options(station: str) -> dict[tuple, list[str]]:
    dists = distances(station)
    st_obj = get_station(station)
    opts = {}
    for s, d in dists.items():
        if s == station or s in exclude or (len(possible) != 0 and s not in possible): continue

        s_obj = get_station(s)
        l = line_info(s_obj["lines"], st_obj["lines"])

        k = ()
        if ZONES:
            k = (d, l, zone_info(s_obj["zone"], st_obj["zone"]))
        else:
            k = (d, l)
        
        if k in opts.keys():
            opts[k].append(s)
        else:
            opts[k] = [s]
    return opts

def num_options(station: str) -> list[int]:
    return list(map(lambda x: len(x[1]), options(station).items()))

def score(station: str) -> float:
    opts = num_options(station)
    if len(opts) == 0: return 0.0 # this is the only possible station
    avg = sum(opts)/len(opts)
    return avg

def get_possible(guess: dict) -> list[str]:
    k = ()
    if ZONES:
        k = (guess["distance"], guess["line"], guess["zone"])
    else:
        k = (guess["distance"], guess["line"])
    return options(guess["station"])[k]

def join_possible(a: list[str], b: list[str]) -> list[str]:
    r = []
    for i in a:
        if i in b:
            r.append(i)
    return r

try:
    city_file = open("data/cities.json", "r", encoding="utf-8")
except FileNotFoundError:
    print(f"{RED}Please download map data via the download.py script, or from https://networkle.fun/data/cities.json{RESET}")
    exit(1)
cities = json.load(city_file)
city_file.close()
def get_city(city: str) -> dict:
    return list(filter(lambda x: x["id"] == city, cities))[0]

cmd = argparse.ArgumentParser(description="Networkle bot")
all_cities = list(map(lambda x: x["id"], cities))
cmd.add_argument("map", choices=all_cities, help="the map to use")
cmd.add_argument("-s", "--solver", action="store_true", help="interactive solver mode: the bot outputs the next guess, you input how it went.")
cmd.add_argument("-a", "--analyzer", action="store_true", help="analyzer mode: analyzes how well you guessed in an already played game.")
cmd.add_argument("-g", "--guesses", default="[]", help='JSON format, [{"station":"Oxford Circus", "distance":2, "line":0, "zone":1}]. line is one of: 0 - incorrect line, 1 - correct line, 2 - correct color, incorrect line. zone is one of: 0 - target zone is smaller, 1 - correct zone, 2 - target zone is larger')
cmd.add_argument("--guess-file", default="", help="the file to read guess data from. data is in the same format as -g.")

args = cmd.parse_args()

MAP = args.map
ZONES = get_city(MAP)["hasZones"]
COLORS = "hasLineGroups" in get_city(MAP).keys() and get_city(MAP)["hasLineGroups"]

# load the data
try:
    map_file = open(f"data/{MAP}.json", "r", encoding="utf-8")
except FileNotFoundError:
    print(f"{RED}Please download map data via the download.py script, or from https://networkle.fun/data/{MAP}.json{RESET}")
    exit(1)
data = json.load(map_file)

if COLORS:
    line_data = get_city(MAP)["lineGroups"]
    for k, v in line_data.items():
        for l in v:
            lines[l] = k

# load the guesses
guesses = json.loads(args.guesses)
if args.guess_file != "":
    with open(args.guess_file, "r", encoding="utf-8") as f:
        guesses = json.load(f)
exclude = list(map(lambda x: x["station"], guesses))

# select possible stations based on the already made guesses
def calc_possible(guesses: list[dict]) -> list[str]:
    global exclude
    exclude = list(map(lambda x: x["station"], guesses))
    possible = []
    if len(guesses) > 0:
        possible = get_possible(guesses[0])
        for guess in guesses[1:]:
            possible = join_possible(possible, get_possible(guess))
    return possible

# calculate the score for each station
# the score is just the average number of possible stations it leaves after guessing it, so lower is better
def calc_scores(silent=False, beginning="calculating scores... ", newline=True) -> dict[str, float]:
    scores = {}
    n = len(data)
    for i, s in enumerate(data):
        name = s["name"]
        if not silent: print(f"{BOLD}{beginning}{int(((i+1)/n)*100)}%{RESET}", end="\r")
        if name in exclude or (len(possible) != 0 and name not in possible): continue
        scores[name] = score(name)
    if not silent and newline: print()
    return scores

def display_score(i: int, s: tuple[str, float], bold=False):
    b = BOLD if bold else ""
    return "{BOLD}{YELLOW}{i:<4} {GREEN}{name:<35}{BLUE}{score:0<4.3}{RESET}".format(i=str(i)+".", name=s[0], score=s[1], GREEN=GREEN, BLUE=BLUE, YELLOW=YELLOW, BOLD=b, RESET=RESET)

# display the scores
def display_scores(scores: dict[str, float], highlight=[]):
    best = list(scores.items())
    best.sort(key=lambda x: x[1])

    n = len(best)
    print("{BOLD}     {STATION:<34}SCORE{RESET}".format(BOLD=BOLD, RESET=RESET, STATION="STATION"))
    dots = False
    for i, s in enumerate(best):
        if i < 5 or s[0] in highlight or n-i-1 < 1:
            if s[0] in highlight:
                print(display_score(i+1, best[i], bold=True))
            else:
                print(display_score(i+1, best[i]))
            dots = False
        else:
            if not dots:
                print(f"{BOLD}...{RESET}")
                dots = True

if args.solver:
    guess_num = 1
    print(f"{BOLD}Use Ctrl+C at any time to quit.{RESET}")
    while True:
        print(f"{BOLD}Guess {guess_num}:{RESET}")
        guess_num += 1
        possible = calc_possible(guesses)
        scores = calc_scores()
        display_scores(scores)
        if len(scores) == 1:
            print(f"{BOLD}Please guess the provided station, then you should win.{RESET}")
            break
        used_guess = min(list(scores.items()), key=lambda x: x[1])[0]
        while True:
            used_best = input(f"{BOLD}Did you use the best guess provided by the bot ({used_guess})? [Y/n] {RESET}")
            if used_best.lower() in ["n", "no", "false"]:
                while True:
                    used_guess = input(f"{BOLD}Which station did you guess? {RESET}")
                    if used_guess not in list(map(lambda x: x["name"], data)):
                        print(f"{BOLD}This station does not exist.{RESET}")
                    else: break
                break
            elif used_best.lower() in ["", "y", "yes", "true"]:
                break
            else:
                print(f"{BOLD}Please type in either 'y' or 'n'.{RESET}")
                exit(1)
        distance = 0
        while True:
            d = input(f"{BOLD}What is the stop distance? {RESET}")
            try:
                distance = int(d)
                break
            except ValueError:
                print(f"{BOLD}Please input a valid integer.{RESET}")
        line = 0
        while True:
            l = input(f"{BOLD}Correct line? [y/n/correct [c]olor, incorrect line] {RESET}")
            if l in ["y", "yes"]:
                line = 1
                break
            elif l in ["n", "no"]:
                line = 0
                break
            elif l in ["c"]:
                if COLORS:
                    line = 2
                    break
                else:
                    print(f"{BOLD}This map does not have color information.{RESET}")
            else:
                print(f"{BOLD}Please enter only 'y', 'n', or 'c'.{RESET}")
        zone = 0
        if ZONES:
            while True:
                z = input(f"{BOLD}Zone information? [[l]ess/[g]reater/[e]qual] {RESET}")
                if z in ["l", "less"]:
                    zone = 0
                    break
                elif z in ["g", "greater"]:
                    zone = 2
                    break
                elif z in ["e", "equal"]:
                    zone = 1
                    break
                else:
                    print(f"{BOLD}Please enter only 'l', 'g', or 'e'.{RESET}")
        guess = {
            "station": used_guess,
            "distance": distance,
            "line": line,
        }
        if ZONES:
            guess["zone"] = zone
        guesses.append(guess)
elif args.analyzer:
    if len(guesses) == 0:
        print(f"{RED}{BOLD}Please use -g to input your guesses.{RESET}")
        exit(1)
    if guesses[-1]["distance"] != 0:
        print(f"{RED}{BOLD}The last guess should be your winning guess, with a stop distance of 0.{RESET}")

    cur_guesses = []
    analysis = []
    first_scores = {}
    first = True
    for i, g in enumerate(guesses):
        possible = calc_possible(cur_guesses)
        human_guess_possible = True
        if len(possible) != 0 and g["station"] not in possible:
            possible.append(g["station"])
            human_guess_possible = False
        scores = calc_scores(beginning="Calculating Networkle Bot's guesses... ", newline=False)
        if first:
            first_scores = scores
            first = False
        cur_guess = min(list(filter(lambda x: human_guess_possible or (not human_guess_possible and x[0] != g["station"]), scores.items())), key=lambda x: x[1])
        human_score = list(filter(lambda x: x[0] == g["station"], scores.items()))[0][1]
        analysis.append((scores, g["station"], human_guess_possible, human_score, cur_guess[0], cur_guess[1]))
        cur_guesses.append(g)

    cur_guesses = []
    bot_guesses = []
    answer = guesses[-1]["station"]
    first = True
    while True:
        scores = {}
        if first:
            scores = first_scores
            first = False
        else:
            possible = calc_possible(cur_guesses)
            scores = calc_scores(beginning="Calculating Networkle Bot's guesses... ", newline=False)
        cur_guess = min(list(scores.items()), key=lambda x: x[1])
        station = cur_guess[0]
        if station == answer:
            bot_guesses.append({"station": station, "distance": 0, "line": 1, "zone": 1})
            break
        distance = distances(station)[answer]
        line = line_info(get_station(station)["lines"], get_station(answer)["lines"])
        g = {"station": station, "distance": distance, "line": line}
        if ZONES:
            zone = zone_info(get_station(answer)["zone"], get_station(station)["zone"])
            g["zone"] = zone
        bot_guesses.append(g)
        cur_guesses.append(g)

    print(f"{BOLD}Calculating Networkle Bot's guesses... {RESET}")
    for i, g in enumerate(guesses):
        a = analysis[i]
        bot_only_possible = len(a[0]) == 1 or (len(a[0]) == 2 and not a[2])
        human_only_possible = len(a[0]) == 1

        print(f"{BOLD}Guess {i+1}:{RESET}")
        print(f"{BOLD}You picked {RESET}{GREEN}{g['station']}{RESET}{BOLD}", end="")

        if not human_only_possible:
            print(f", which would leave {RESET}{BLUE}{str(a[3])[:4]}{RESET}{BOLD} possible stations on average{f', {RED}but is not a possible answer' if not a[2] else ''}. {RESET}", end="")
        else:
            print(f", which was the only possible answer at this point{RESET}. ", end="")

        print(f"{BOLD}Networkle Bot would've picked {RESET}{GREEN}{a[4]}{RESET}{BOLD}", end="")
        if not bot_only_possible:
            print(f", which would leave {RESET}{BLUE}{str(a[5])[:4]}{RESET}{BOLD} possible stations on average.{RESET}")
        else:
            print(f", which was the {RED if not human_only_possible else ""}only possible answer at this point{RESET}")
        
        if not bot_only_possible: display_scores(a[0], highlight=[a[1], a[4]])
        print()
    
    print(f"{BOLD}How Networkle Bot would've solved this puzzle (green - correct line; yellow - incorrect line, correct color; white - incorrect line):{RESET}")
    for g in bot_guesses:
        zones = get_station(g["station"])["zone"] if ZONES else ""
        print("{color}{station:<40}{distance:<4}{zone}{RESET}".format(color=["", GREEN, YELLOW][g["line"]], station=g["station"], distance=g["distance"], zone=(["<", "=", ">"][g["zone"]]+" zone "+(" or ".join(zones) if type(zones) == list else str(zones)) if ZONES else ""), RESET=RESET))
    print()

    skill = 0
    luck = 1
    n = 0
    for i, a in enumerate(analysis):
        worst = max(list(a[0].items()), key=lambda x: x[1])[1]
        if a[5] != 0:
            n += 1
            maximum = worst/a[5]
            actual = a[3]/a[5]
            increment = (worst-actual)/(worst-1) if worst > 1.001 else 0
            if not a[2]: increment -= increment/(len(a[0])-1)
            skill += max(increment, 0)

        next = analysis[i+1] if i < len(analysis)-1 else []
        if next != []:
            x = len(next[0])
            if not next[2]: x -= 1
            if x != 0:
                luck *= a[3] / x
    skill /= n
    skill = int(100*skill)
    luck = int(100*luck)
    print(f"{BOLD}OVERALL SUMMARY:{RESET}")
    print(f"{BOLD}{YELLOW}SKILL: {RESET}{BLUE}{skill}/100{RESET}")
    print(f"{BOLD}{YELLOW}LUCK: {RESET}{BLUE}{luck} where 100 is average{RESET}")
else:
    possible = calc_possible(guesses)
    scores = calc_scores()
    display_scores(scores)