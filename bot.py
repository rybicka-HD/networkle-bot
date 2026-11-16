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
            for n in get_station(s)["adjacent"]:
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
    print(f"{RED}Please download map data from https://networkle.fun/data/cities.json{RESET}")
    exit(1)
cities = json.load(city_file)
city_file.close()
def get_city(city: str) -> dict:
    return list(filter(lambda x: x["id"] == city, cities))[0]

cmd = argparse.ArgumentParser(description="Networkle bot")
all_cities = list(map(lambda x: x["id"], cities))
cmd.add_argument("map", choices=all_cities, help="the map to use")
cmd.add_argument("-g", "--guesses", default="[]", help='JSON format, [{"station":"Oxford Circus", "distance":2, "line":0, "zone":1}]. line is one of: 0 - incorrect line, 1 - correct line, 2 - correct color, incorrect line. zone is one of: 0 - target zone is smaller, 1 - correct zone, 2 - target zone is larger')

args = cmd.parse_args()

MAP = args.map
ZONES = get_city(MAP)["hasZones"]
COLORS = get_city(MAP)["hasLineGroups"]

# load the data
try:
    map_file = open(f"data/{MAP}.json", "r", encoding="utf-8")
except FileNotFoundError:
    print(f"{RED}Please download map data from https://networkle.fun/data/{MAP}.json{RESET}")
    exit(1)
data = json.load(map_file)

if COLORS:
    line_data = get_city(MAP)["lineGroups"]
    for k, v in line_data.items():
        for l in v:
            lines[l] = k

# load the guesses
guesses = json.loads(args.guesses)
exclude = list(map(lambda x: x["station"], guesses))

# select possible stations based on the already made guesses
def calc_possible(guesses: list[dict]) -> list[str]:
    possible = []
    if len(guesses) > 0:
        possible = get_possible(guesses[0])
        for guess in guesses[1:]:
            possible = join_possible(possible, get_possible(guess))
    return possible

# calculate the score for each station
# the score is just the average number of possible stations it leaves after guessing it, so lower is better
def calc_scores() -> dict[str, float]:
    scores = {}
    n = len(data)
    for i, s in enumerate(data):
        name = s["name"]
        print(f"{BOLD}calculating scores... {int(((i+1)/n)*100)}%{RESET}", end="\r")
        if name in exclude or (len(possible) != 0 and name not in possible): continue
        scores[name] = score(name)
    print()
    return scores

def display_score(i: int, s: tuple[str, float]):
    return "{YELLOW}{i:<4} {GREEN}{name:<35}{BLUE}{score:0<4.3}{RESET}".format(i=str(i)+".", name=s[0], score=s[1], GREEN=GREEN, BLUE=BLUE, YELLOW=YELLOW, RESET=RESET)

# display the scores
def display_scores(scores: dict[str, float]):
    best = list(scores.items())
    best.sort(key=lambda x: x[1])

    n = len(best)
    print("{BOLD}     {STATION:<34}SCORE{RESET}".format(BOLD=BOLD, RESET=RESET, STATION="STATION"))
    dots = False
    for i, s in enumerate(best):
        if i < 5 or s[0] == "Times Square - 42 St" or i == n-1:
            print(display_score(i+1, best[i]))
            dots = False
        else:
            if not dots:
                print(f"{BOLD}...{RESET}")
                dots = True

possible = calc_possible(guesses)
scores = calc_scores()
display_scores(scores)