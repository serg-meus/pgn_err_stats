#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pgn_err_stats v.0.4

Console based tool for automatic analysis of chess games with an external
UCI engine (see README.md)
"""
from time import time
from subprocess import Popen, PIPE
from os import path
from sys import stderr, exit
from json import load
from multiprocessing import Pool
from chess import pgn, Move


def main():
    with open('pgn_err_stats.json', 'r', encoding='utf-8') as infile:
        jsn = load(infile)

    print('Reading games...')
    uci_games, headers = pgn_to_uci(jsn)
    t_start = time()
    if not jsn['read_values_from_pgn_input']:
        results = analyze_and_save(uci_games, headers, jsn)
    else:
        results = get_values_from_pgn(jsn['pgn_input'], jsn['first_game'],
                                      jsn['last_game'])
    stats = get_stats(headers, results, jsn)
    out_stats(stats, jsn['only_if_player_name_contains'])
    print('\nAnalysis time: %.2f s' % (time() - t_start))
    return 0


def analyze_and_save(uci_games, headers, jsn):
    analyze_game.game_cr = 0
    if not path.isfile(jsn['engine']):
        stderr.write('Error: engine executable not found\n')
        exit(1)
    progress_bar(0, len(uci_games), 'Analyzing:')
    if jsn['cpu_cores'] != '1':
        results = analyze_games_parallel(uci_games, jsn)
    else:
        results = analyze_games(uci_games, jsn)
    if not results:
        stderr.write('Error: cant execute the engine\n')
        exit(2)
    if jsn['pgn_output'] and jsn['pgn_output'] != jsn['pgn_input']:
        write_pgn(uci_games, headers, results, jsn['pgn_output'])
    return results


def analyze_games(uci_games, jsn):
    ans = []
    for game in uci_games:
        result = analyze_game(game, jsn, len(uci_games))
        ans.append(result)
    return ans


def analyze_games_parallel(uci_games, jsn):
    with Pool(int(jsn['cpu_cores'])) as p:
        ans = p.starmap(analyze_game, ((i, jsn, len(uci_games))
                                        for i in uci_games))
    print()
    return ans


def analyze_game(game, jsn, n_games):
    with Popen(jsn['engine'], shell=True, stdin=PIPE, stdout=PIPE) as pipe:
        pipe_response(pipe, 'uci', 'uciok')
        pipe_response(pipe, 'ucinewgame')
        ans = [analyze_position(pipe, None, jsn['level'])]
        for halfmove_num in range(len(game)):
            moves = ' '.join(game[:halfmove_num + 1])
            ans.append(analyze_position(pipe, moves, jsn['level']))
        if ans[-1][0] == 'mate' and ans[-1][1] == '0':
            del(ans[-1])
        pipe_response(pipe, 'quit')
        analyze_game.game_cr += 1
        progress_bar(analyze_game.game_cr, n_games, 'Analyzing:')
        return ans
    return None


def analyze_position(pipe, moves, level):
    pipe_response(pipe, 'isready', 'readyok')
    pipe_response(pipe, 'position startpos moves ' + moves if moves else
                  'position startpos')
    pipe_response(pipe, 'isready', 'readyok')
    out = pipe_response(pipe, 'go ' + level, 'bestmove')
    return analysis_result(out)


def get_stats(headers, result, jsn):
    ans = {}
    for hdr, res in zip(headers, result):
        for side in ('White', 'Black'):
            stat = get_stat(res, side, jsn)
            if not stat:
                continue
            if hdr[side] not in ans:
                ans[hdr[side]] = stat
            else:
                ans[hdr[side]] = update_stat(ans[hdr[side]], stat)
    return ans


def get_stat(result, side, jsn):
    sum_cp_loss, inaccs, mistakes, blunders = 0, 0, 0, 0
    first = int(jsn['skip_first_moves']) if jsn['skip_first_moves'] else 0
    res1 = get_list_of_lists(result, side, first)
    if not res1 or len(res1) == 0:
        return None
    for ans in res1:
        cp1 = int(ans[0][1]) if ans[0][0] == 'cp' else 32000
        cp2 = -int(ans[1][1]) if ans[1][0] == 'cp' else 32000
        cp_loss = cp1 - cp2 if cp2 < cp1 else 0
        sum_cp_loss += cp_loss if ans[1][0] == ans[0][0] == 'cp' else 0
        if cp_loss >= int(jsn['blunder']):
            blunders += 1
        elif cp_loss >= int(jsn['mistake']):
            mistakes += 1
        elif cp_loss >= int(jsn['inaccuracy']):
            inaccs += 1
    return sum_cp_loss/len(res1), inaccs, mistakes, blunders, 1, len(res1)


def get_list_of_lists(result, side, first):
    ans1 = result[2*first:]
    if not ans1:
        return None
    if side == 'Black':
        del(ans1[0])
    ans2 = [ans1[i:i + 2] for i in range(0, len(ans1), 2)]
    if len(ans2[-1]) == 1:
        del(ans2[-1])
    return ans2


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
    with open(jsn['pgn_input']) as file:
        while game_cr < last:
            game = pgn.read_game(file)
            if not game:
                break
            if player and player not in game.headers['White'].lower() and \
                    player not in game.headers['Black'].lower():
                continue
            game_cr += 1
            if game_cr < first:
                continue
            line = game.mainline()
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
    with open(in_file) as file:
        while game_cr <= last:
            line = file.readline()
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
            if '.' not in tmp[-1]:
                del(tmp[-1])
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
        game = pgn.Game()
        game.headers = header
        node = game.add_variation(Move.from_uci(uci_game[0]),
                                  comment=res_to_str(result[0]))
        for i, move in enumerate(uci_game[1:]):
            node = node.add_variation(Move.from_uci(uci_game[1 + i]),
                                      comment=res_to_str(result[1 + i]))
        exporter = pgn.StringExporter()
        pgn_string += game.accept(exporter) + '\n\n'
    with open(out_file, 'w') as file:
        file.write(pgn_string)


def res_to_str(res):
    if res[0] == 'cp':
        score = '{:.2f}'.format(int(res[1])/100)
    elif res[0] == 'mate':
        score = ('+' if int(res[1]) > 0 else '-') + 'M' + \
            res[1].replace('+', '').replace('-', '')
    else:
        return None
    return score + '/' + res[3] + ' ' + res[2]


def progress_bar(cur, total, prefix='Progress:', suffix='Finished',
                 decimals=1, length=50, fill='█', end='\r'):
    def _print_progress_bar(iteration):
        percent = ('{0:.' + str(decimals) +
                   'f}').format(100*(iteration/float(total)))
        filled_length = int(length*iteration // total)
        bar = fill*filled_length + '-'*(length - filled_length)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=end)

    _print_progress_bar(cur) if cur <= total else print()


def test():
    jsn = {"first_game": "",
           "last_game": "",
           "skip_first_moves": "",
           "only_if_player_name_contains": "",
           "inaccuracy": "50",
           "mistake": "100",
           "blunder": "300" }
    results = get_values_from_pgn('test_games.pgn', '', '')
    headers = [{'White': 'Player1', 'Black': 'Player2'}]
    stats = get_stats(headers, results, jsn)
    assert stats == {'Player1': (400., 0, 0, 1, 1, 3),
                     'Player2': (370., 0, 0, 1, 1, 3)}

if __name__ == '__main__':
    test()
    main()
