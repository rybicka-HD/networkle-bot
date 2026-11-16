import json

MAP = "newyork"
ZONES = False
COLORS = True

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

# load the data
with open(f"{MAP}.json", "r", encoding="utf-8") as file:
    data = json.load(file)
if COLORS:
    with open("cities.json", "r", encoding="utf-8") as file:
        line_data = list(filter(lambda x: x["id"] == MAP, json.load(file)))[0]["lineGroups"]
        for k, v in line_data.items():
            for l in v:
                lines[l] = k

# load the guesses
exclude = list(map(lambda x: x["station"], guesses))

# select possible stations based on the already made guesses
if len(guesses) > 0:
    possible = get_possible(guesses[0])
    for guess in guesses[1:]:
        possible = join_possible(possible, get_possible(guess))

# calculate the score for each station
# the score is just the average number of possible stations it leaves after guessing it, so lower is better
scores = {}
n = len(data)
for i, s in enumerate(data):
    name = s["name"]
    if name in exclude or (len(possible) != 0 and name not in possible): continue
    print(f"station {i+1}/{n}  {name}           ", end="\r")
    scores[name] = score(name)
print()

# display the scores
best = list(scores.items())
best.sort(key=lambda x: x[1])

def str_best(i: int, s: tuple[int, int]):
    return "{i:<4} {name:<35}{score:0<4.3}".format(i=str(i)+".", name=s[0], score=s[1])

n = len(best)
for i, s in enumerate(best):
    if i < 5 or s[0] == "Times Square - 42 St" or i == n-1:
        print(str_best(i+1, best[i]))
    if i == 5:
        print("...")
