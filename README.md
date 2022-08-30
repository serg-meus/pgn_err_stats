pgn-err-stats v.0.6
===================

GUI tool for automatic analysis of chess games with an external UCI engine.

After setting up the parameters the tool saves to log file the statistics of
each player: number of analyzed games, moves, blunders, mate blunders,
mistakes, inaccuracies and average loss per move in centipawns from
the engine point of view.

By default, each position is analyzed in 0.5 seconds. This may be changed by
option "level" in json file. You can also use options "depth 10" or
"nodes 5000" for extra-fast analyzes, the numbers may vary.

Author: Sergey Meus, Russian Federation.

Link for download executables:
    https://github.com/serg-meus/pgn_err_stats/releases/tag/v0.6

Dependencies (Python libs): python-chess

Command to install: pip install python-chess

If the last command fails, you should check python and pip via
commands```python3 --version``` and ```pip3 --version``` and find instructions
to install python3 and pip3 packages for your system.

Command to launch python version: ```python pgn-err-stats.pyw```, in Windows
double-click on pyw file must also work.

License: GNU GPL v3.0
