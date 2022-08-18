Pgn_err_stats v.0.1
===================

Console based tool for automatic analysis of chess games with an external
UCI engine.

After setting up the parameters of analysis (see pgn_err_stats.json file) and
executing, this script prints to console the statistics of each player:
number of analyzed games, moves, blunders, mistakes, inaccuracies and
average loss per move in centipawns from the engine point of view.

By default, each position is analyzed in 0.5 seconds. This may be changed by
option "level" in json file. You can also use options "depth 10" or
"nodes 5000" for extra-fast analyzes, the numbers may vary.


Typical usage:

1. Open pgn_err_stats.json and set up parameters of analysis, path to engine,
etc

2. Open terminal (command promt) and change current directory to path
containing the tool

3. Execute command (for Win64 version): pgn_err_stats.exe
For Python version execute command: python pgn_err_stats.py
To save analysis result into a file, add ' > filename.txt' after the command.

Author: Sergey Meus, Russian Federation.

Links for download Win64 executable:
    https://github.com/serg-meus/pgn_err_stats/tag/01

Dependencies (Python libs): python-chess
Command to install: pip install python-chess

License: GNU GPL v3.0