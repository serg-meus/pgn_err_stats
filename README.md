Pgn_err_stats v.0.3
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

2. Open terminal (command promt) and enter commands to change current
directory to path containing the tool

3. Execute command ```pgn_err_stats.exe``` (for Win64 version)
or ```python pgn_err_stats.py``` (to run Python script).

To save analysis result into a file, add ' > filename.txt' after the command,
for instance: ```pgn_err_stats.exe > filename.txt```

Author: Sergey Meus, Russian Federation.

Link for download executables:
    https://github.com/serg-meus/pgn_err_stats/releases/tag/03

Dependencies (Python libs): python-chess, joblib

Command to install: pip install python-chess joblib

If the last command fails, you should check python and pip via
commands```python3 --version``` and ```pip3 --version``` and find instructions
to install python3 and pip3 packages for your system.

License: GNU GPL v3.0
