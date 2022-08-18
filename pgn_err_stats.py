#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pgn_err_stats v.0.1

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
    https://github.com/serg-meus/pgn_err_stats/releases/tag/01

Dependencies (Python libs): python-chess
Command to install: pip install python-chess

License: GNU GPL v3.0
"""

from subprocess import Popen, PIPE
from os import path
from sys import stderr, exit
from json import load
import chess
import chess.pgn


def main():
    with open('pgn_err_stats.json', 'r', encoding='utf-8') as infile:
        jsn = load(infile)

    uci_games, headers = pgn_to_uci(jsn)
    if not jsn['read_values_from_pgn_input']:
        results = analyze_and_save(uci_games, headers, jsn)
    else:
        results = get_values_from_pgn(jsn['pgn_input'], jsn['first_game'],
                                      jsn['last_game'])
    stats = get_stats(headers, results, jsn)
    out_stats(stats, jsn['only_if_player_name_contains'])
    return 0


def analyze_and_save(uci_games, headers, jsn):
    if not path.isfile(jsn['engine']):
        stderr.write('Error: engine executable not found\n')
        exit(1)
    results = start_engine_and_analyze(uci_games, jsn)
    if not results:
        stderr.write('Error: cant execute the engine\n')
        exit(2)
    if jsn['pgn_output'] and jsn['pgn_output'] != jsn['pgn_input']:
        write_pgn(uci_games, headers, results, jsn['pgn_output'])
    return results


def start_engine_and_analyze(uci_games, jsn):
    with Popen(jsn['engine'], shell=True, stdin=PIPE, stdout=PIPE) as pipe:
        pipe_response(pipe, 'uci', 'uciok')
        pipe_response(pipe, 'ucinewgame')
        results = analyze_games(pipe, uci_games, jsn['level'])
        pipe_response(pipe, 'quit')
        return results
    return None


def get_stats(headers, result, jsn):
    ans = {}
    for hdr, res in zip(headers, result):
        for side in ('White', 'Black'):
            stat = get_stat(res, side, jsn)
            if hdr[side] not in ans:
                ans[hdr[side]] = stat
            else:
                ans[hdr[side]] = update_stat(ans[hdr[side]], stat)
    return ans


def get_stat(result, side, jsn):
    sum_cp_loss, inaccs, mistakes, blunders = 0, 0, 0, 0
    first = jsn['skip_first_moves']
    first = int(first) if first else 0
    ans = result[2*first:]
    shft = 1 if side == 'Black' else 0
    for i in range(int(len(ans)/2) - 1):
        if ans[2*i + shft + 1][0] != 'cp':
            break
        cp1 = int(ans[2*i + shft][1])
        cp2 = -int(ans[2*i + shft + 1][1])
        cp1, cp2 = (-cp1, -cp2) if side == 'Black' else (cp1, cp2)
        cp_loss = cp1 - cp2 if cp2 < cp1 else 0
        sum_cp_loss += cp_loss
        if cp_loss >= int(jsn['blunder']):
            blunders += 1
        elif cp_loss >= int(jsn['mistake']):
            mistakes += 1
        elif cp_loss >= int(jsn['inaccuracy']):
            inaccs += 1

    return sum_cp_loss/len(ans), inaccs, mistakes, blunders, 1, len(ans)


def update_stat(old, new):
    avg_cp_loss = (old[0]*old[5] + new[0]*new[5])/(old[5] + new[5])
    ans = [x + y for x, y in zip(old, new)]
    ans[0] = avg_cp_loss
    return ans


def out_stats(stats, player_name):
    ans = {k: v for k, v in sorted(stats.items(), key=lambda item: item[1][4],
                                   reverse=True)}
    if player_name:
        ans = {k: v for k, v in ans.items() if player_name in k.lower()}
    for i, a in enumerate(ans):
        print('%d. %s. Games: %d, Moves: %d, Blunders: %d, Mistakes: %d, '
              'Inaccuracies: %d, Average loss: %.1f centipawns' %
              (i + 1, a, ans[a][4], ans[a][5], ans[a][3], ans[a][2], ans[a][1],
               ans[a][0]))


def analyze_games(pipe, uci_games, level):
    ans = []
    for game in progress_bar(uci_games, prefix='Analysis:', suffix='Games'):
        ans_game = [analyze_position(pipe, None, level)]
        for halfmove_num in range(len(game)):
            moves = ' '.join(game[:halfmove_num + 1])
            ans_game.append(analyze_position(pipe, moves, level))
        ans.append(ans_game)
    return ans


def analyze_position(pipe, moves, level):
    pipe_response(pipe, 'isready', 'readyok')
    pipe_response(pipe, 'position startpos moves ' + moves if moves else
                  'position startpos')
    pipe_response(pipe, 'isready', 'readyok')
    out = pipe_response(pipe, 'go ' + level, 'bestmove')
    return analysis_result(out)


def pgn_to_uci(jsn):
    uci_games = []
    headers = []
    game_cr = 0
    first, last = jsn['first_game'], jsn['last_game']
    player = jsn['only_if_player_name_contains'].lower()
    if not first or not last or int(first) <= 0 or int(last) <= 0:
        first, last = 1, int(1e9)
    else:
        first, last = int(first), int(last)
    with open(jsn['pgn_input']) as pgn:
        while game_cr < last:
            game = chess.pgn.read_game(pgn)
            if not game:
                break
            if player and player not in game.headers['White'].lower() and \
                    player not in game.headers['Black'].lower():
                continue
            game_cr += 1
            if game_cr < first:
                continue
            line = game.main_line()
            uci_games.append([m.uci() for m in line])
            headers.append(game.headers)
    return uci_games, headers


def get_values_from_pgn(in_file, first, last):
    results, ans = [], []
    game_cr = 0
    if not first or not last or int(first) > int(last) or \
            int(first) <= 0 or int(last) <= 0:
        first, last = 1, int(1e9)
    else:
        first, last = int(first), int(last)
    with open(in_file) as pgn:
        while game_cr <= last:
            line = pgn.readline()
            if not line:
                break
            if '[Event' in line:
                game_cr += 1
                results.append(ans)
                ans = []
            if '{' not in line:
                continue
            tmp = [x.split('/')[0] for x in line.split() if '/' in x and
                   'M' not in x]
            ans += [['cp', str(int(float(x)*100))] for x in tmp]
        results.append(ans)
    return results[1:]


def pipe_response(proc, command, last_out_contains=None):
    proc.stdin.write((command + '\n').encode())
    proc.stdin.flush()
    if last_out_contains is None:
        return None
    elif last_out_contains == '':
        return proc.stdout.readline().decode()
    else:
        out = []
        while True:
            line = proc.stdout.readline().decode()
            out.append(line)
            if last_out_contains in line:
                break
        return out


def analysis_result(out):
    for o in out[::-1]:
        if 'score' in o:
            score = o.split('score ')[1].split()[0:2]
            bestmove = out[-1].split()[1]
            depth = o.split('depth ')[1].split()[0]
            nodes = o.split('nodes ')[1].split()[0] if 'nodes ' in o else ''
            return score + [bestmove] + [depth] + [nodes]


def write_pgn(uci_games, headers, results, out_file):
    pgn_string = ''
    for uci_game, header, result in zip(uci_games, headers, results):
        game = chess.pgn.Game()
        game.headers = header
        node = game.add_variation(chess.Move.from_uci(uci_game[0]),
                                  comment=res_to_str(result[0]))
        for i, move in enumerate(uci_game[1:]):
            node = node.add_variation(chess.Move.from_uci(uci_game[1 + i]),
                                      comment=res_to_str(result[1 + i]))
        exporter = chess.pgn.StringExporter()
        pgn_string += game.accept(exporter) + '\n\n'
    with open(out_file, 'w') as pgn:
        pgn.write(pgn_string)


def res_to_str(res):
    if res[0] == 'cp':
        score = '{:.2f}'.format(int(res[1])/100)
    elif res[0] == 'mate':
        score = ('+' if int(res[1]) > 0 else '-') + 'M' + \
            res[1].replace('+', '').replace('-', '')
    else:
        return None
    return score + '/' + res[3] + ' ' + res[2]


def progress_bar(iterable, prefix='Progress:', suffix='Finished', decimals=1,
                 length=50, fill='█', end='\r'):
    total = len(iterable)

    def _print_progress_bar(iteration):
        percent = ('{0:.' + str(decimals) +
                   'f}').format(100*(iteration/float(total)))
        filled_length = int(length*iteration // total)
        bar = fill*filled_length + '-'*(length - filled_length)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=end)

    _print_progress_bar(0)
    for i, item in enumerate(iterable):
        yield item
        _print_progress_bar(i + 1)
    print()


if __name__ == '__main__':
    main()
