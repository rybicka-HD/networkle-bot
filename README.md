# Networkle Bot

This is a bot for the game [networkle](https://networkle.fun/). It supports three modes:
 - **standard mode**: You input the guesses you already made and it will tell you the next best move.
 - **solver mode (`-s`)**: This is how you let it play a game completely, it tells you the next guess and you tell the bot how it went.
 - **analyzer mode (`-a`)**: You input the guesses from a game you already finished and it tells you how good your guesses were.

It works just by looking at how many possible stations will be left on average after each possible guess.

To run it, just run the `bot.py` file. It has no dependecies besides the standard library. The map data from the game should already be present in the `data` directory. If it isn't, or to update it, run the `download.py` script from the root directory of the project.

Unfortunately, the London tube-only map doesn't work because the game uses the same `london.json` for the full network and the tube-only network. I don't know how the game works with that internally, and I don't feel like implementing it here.