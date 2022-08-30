#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pgn-err-stats v.0.5

  GUI tool for automatic analysis of chess games with an external UCI engine
(see README.md)
"""

import tkinter as tk
from tkinter import messagebox, filedialog as fd, ttk
from time import time
from subprocess import call, Popen, PIPE
from platform import system
import os
import sys
from multiprocessing import Pool
from json import load, dumps
from chess import pgn, Move


def main():
    root = tk.Tk()
    root.option_add("*Label.Font", "clearlyu 13")
    root.title("pgn-err-stats v0.5")
    root.resizable(False, False)
    main.gui_items = create_gui_items()
    main.stdout = sys.stdout
    main.stderr = sys.stderr
    main.root = root
    root.protocol('WM_DELETE_WINDOW', on_exit)
    root.mainloop()


def create_gui_items():
    opt = {
        "pgn_input": "",
        "pgn_output": "",
        "engine": "",
        "first_game": "0",
        "last_game": "0",
        "skip_first_moves": "5",
        "only_if_player_name_contains": "",
        "read_values_from_pgn_input": False,
        "level": "movetime 500",
        "cpu_cores": "1",
        "inaccuracy": "50",
        "mistake": "100",
        "blunder": "300",
        "logfile": "logfile.txt"
        }
    if os.path.isfile('pgn-err-stats.json'):
        with open('pgn-err-stats.json', 'r', encoding='utf-8') as infile:
            opt = load(infile)
    items, buttons = init_gui_items()
    set_options(items, opt)
    pack_gui_items(items)
    bind_buttons(buttons)
    return items


def set_text(item, text):
    item.delete(0, tk.END)
    item.insert(0, text)


def init_gui_items():
    items = [[] for i in range(15)]
    buttons = {}

    items[0].append(tk.Label(text='Input PGN file'))
    items[0].append(tk.Entry(width=60))
    items[0].append(tk.Button(text='Open'))

    items[1].append(tk.Label(text='Output PGN file'))
    items[1].append(tk.Entry(width=60))
    items[1].append(tk.Button(text='Open'))

    items[2].append(tk.Label(text='Engine executable'))
    items[2].append(tk.Entry(width=60))
    items[2].append(tk.Button(text='Open'))

    items[3].append(tk.Label(text='First game'))
    var = tk.IntVar(value=0)
    items[3].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=1e9))

    items[4].append(tk.Label(text='Last game'))
    var = tk.IntVar(value=0)
    items[4].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=1e9))

    items[5].append(tk.Label(text='Skip first moves'))
    var = tk.IntVar(value=5)
    items[5].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=200))

    items[6].append(tk.Label(text='Only if player name contains'))
    items[6].append(tk.Entry(width=60))

    items[7].append(tk.Label(text='Read values from PGN input'))
    items[7].append(tk.Label(text="(don't run the engine)"))
    items[7].append(ttk.Checkbutton())
    items[7][2].state(['!alternate', '!selected'])

    items[8].append(tk.Label(text='Level'))
    items[8].append(ttk.Combobox(values=['movetime', 'nodes', 'depth'],
                                 state='readonly'))
    var = tk.IntVar(value=500)
    items[8].append(tk.Spinbox(width=8, textvariable=var, from_=0, to=1e9))
    items[8][1].current(0)

    items[9].append(tk.Label(text='CPU cores'))
    var = tk.IntVar(value=1)
    items[9].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=9999))

    items[10].append(tk.Label(text='Inaccuracy'))
    var = tk.IntVar(value=50)
    items[10].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=9999))

    items[11].append(tk.Label(text='Mistake'))
    var = tk.IntVar(value=100)
    items[11].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=9999))

    items[12].append(tk.Label(text='Blunder'))
    var = tk.IntVar(value=300)
    items[12].append(tk.Spinbox(width=10, textvariable=var, from_=0, to=9999))

    items[13].append(tk.Label(text='Output log file'))
    items[13].append(tk.Entry(width=60))
    items[13].append(tk.Button(text='Open'))

    items[14].append(tk.Label(text=''))
    items[14].append(tk.Button(text='Run'))
    items[14].append(tk.Button(text='Show log'))

    buttons['open_pgn_in'] = items[0][2]
    buttons['open_pgn_out'] = items[1][2]
    buttons['open_engine'] = items[2][2]
    buttons['open_log'] = items[13][2]
    buttons['run'] = items[14][1]
    buttons['show_log'] = items[14][2]

    return items, buttons


def pack_gui_items(items):
    for row, row_items in enumerate(items):
        for col, item in enumerate(row_items):
            item.grid(column=col, row=row, padx=6, pady=4, sticky=tk.W)


def bind_buttons(buttons):
    buttons['run'].bind('<ButtonRelease-1>', on_evaluate)
    buttons['open_pgn_in'].bind('<Button-1>', on_open_pgn_in)
    buttons['open_pgn_out'].bind('<Button-1>', on_open_pgn_out)
    buttons['open_engine'].bind('<Button-1>', on_open_engine)
    buttons['open_log'].bind('<Button-1>', on_open_log)
    buttons['show_log'].bind('<ButtonRelease-1>', on_show_log)


def get_options(items):
    opt = {}
    opt['pgn_input'] = items[0][1].get()
    opt['pgn_output'] = items[1][1].get()
    opt['engine'] = items[2][1].get()
    opt['first_game'] = items[3][1].get()
    opt['last_game'] = items[4][1].get()
    opt['skip_first_moves'] = items[5][1].get()
    opt['only_if_player_name_contains'] = items[6][1].get()
    opt['read_values_from_pgn_input'] = items[7][2].instate(['selected'])
    opt['level'] = items[8][1].get() + ' ' + items[8][2].get()
    opt['cpu_cores'] = items[9][1].get()
    opt['inaccuracy'] = items[10][1].get()
    opt['mistake'] = items[11][1].get()
    opt['blunder'] = items[12][1].get()
    opt['logfile'] = items[13][1].get()

    return opt


def set_options(items, opt):
    set_text(items[0][1], opt['pgn_input'])
    set_text(items[1][1], opt['pgn_output'])
    set_text(items[2][1], opt['engine'])
    set_text(items[3][1], opt['first_game'])
    set_text(items[4][1], opt['last_game'])
    set_text(items[5][1], opt['skip_first_moves'])
    set_text(items[6][1], opt['only_if_player_name_contains'])
    if opt['read_values_from_pgn_input']:
        items[7][2].state(['!alternate', 'selected'])
    else:
        items[7][2].state(['!alternate', '!selected'])
    tmp = {'movetime': 0, 'nodes': 1, 'depth': 2}
    items[8][1].current(tmp[opt['level'].split()[0]])
    set_text(items[8][2], opt['level'].split()[1])
    set_text(items[9][1], opt['cpu_cores'])
    set_text(items[10][1], opt['inaccuracy'])
    set_text(items[11][1], opt['mistake'])
    set_text(items[12][1], opt['blunder'])
    set_text(items[13][1], opt['logfile'])

    return opt


def on_evaluate(event, gui_items=None):
    opt = get_options(main.gui_items)
    sys.stdout, sys.stderr = main.stdout, main.stderr
    if opt['logfile']:
        with open(opt['logfile'], 'w') as log:
            sys.stdout, sys.stderr = log, log
            try:
                evaluate(opt)
            except Exception as Arg:
                messagebox.showerror('Error', 'Something went wrong. '
                                     'See logfile for details')
                log.write(str(Arg))
            else:
                messagebox.showinfo('Success', 'The log file created')
            return 'break'
    evaluate(opt)
    messagebox.showinfo('Success', 'The log file created')
    return 'break'


def evaluate(opt):
    print('Reading games...')
    uci_games, headers = pgn_to_uci(opt)
    t_start = time()
    if not opt['read_values_from_pgn_input']:
        results = analyze_and_save(uci_games, headers, opt)
    else:
        results = get_values_from_pgn(opt['pgn_input'], opt['first_game'],
                                      opt['last_game'])
    stats = get_stats(headers, results, opt)
    out_stats(stats, opt['only_if_player_name_contains'])
    print('\nAnalysis time: %.2f s' % (time() - t_start))


def ini_dir(path):
    if '/' in path.get():
        return '/'.join(path.get().split('/')[:-1])
    else:
        return '.'


def on_open_pgn_in(event, gui_items=None):
    filename = fd.askopenfilename(title='Open file',
                                  initialdir=ini_dir(main.gui_items[0][1]),
                                  filetypes=(('PGN files', '.pgn'),))
    if filename:
        set_text(main.gui_items[0][1], filename)
    return 'break'


def on_open_pgn_out(event, gui_items=None):
    obj = fd.asksaveasfile(initialdir=ini_dir(main.gui_items[1][1]),
                           filetypes=(('PGN files', '.pgn'),))
    if obj and obj.name:
        set_text(main.gui_items[1][1], obj.name)
    return 'break'


def on_open_engine(event, gui_items=None):
    filename = fd.askopenfilename(title='Open file',
                                  initialdir=ini_dir(main.gui_items[2][1]),
                                  filetypes=(('All files', '*'),))
    if filename:
        set_text(main.gui_items[2][1], filename)
    return 'break'


def on_open_log(event, gui_items=None):
    obj = fd.asksaveasfile(initialdir=ini_dir(main.gui_items[13][1]),
                           filetypes=(('Text files', '.txt .log'),))
    if obj and obj.name:
        set_text(main.gui_items[13][1], obj.name)
    return 'break'


def on_exit():
    sys.stdout, sys.stderr = main.stdout, main.stderr
    opt = get_options(main.gui_items)
    json_obj = dumps(opt, indent=4)
    with open('pgn-err-stats.json', 'w', encoding='utf-8') as outfile:
        outfile.write(json_obj)
    main.root.destroy()


def on_show_log(event, gui_items=None):
    filepath = main.gui_items[13][1].get()
    if system() == 'Darwin':        # macOS
        call(('open', filepath))
    elif system() == 'Windows':     # Windows
        os.startfile(filepath)
    else:                           # linux
        call(('xdg-open', filepath))
    return 'break'


def analyze_and_save(uci_games, headers, opt):
    if not os.path.isfile(opt['engine']):
        sys.stderr.write('Error: engine executable not found\n')
        sys.exit(1)
    if opt['cpu_cores'] != '1':
        results = analyze_games_parallel(uci_games, opt)
    else:
        results = analyze_games(uci_games, opt)
    if not results:
        sys.stderr.write('Error: cant execute the engine\n')
        sys.exit(2)
    if opt['pgn_output'] and opt['pgn_output'] != opt['pgn_input']:
        write_pgn(uci_games, headers, results, opt['pgn_output'])
    return results


def analyze_games(uci_games, opt):
    ans = []
    for i, game in enumerate(uci_games):
        result = analyze_game(game, opt, i, len(uci_games))
        ans.append(result)
    return ans


def analyze_games_parallel(uci_games, opt):
    with Pool(int(opt['cpu_cores'])) as p:
        args = [(game, opt, i, len(uci_games))
                for i, game in enumerate(uci_games)]
        ans = p.starmap(analyze_game, args)
    print()
    return ans


def analyze_game(game, opt, game_num, games_total):
    with Popen(opt['engine'], shell=True, stdin=PIPE, stdout=PIPE) as pipe:
        pipe_response(pipe, 'uci', 'uciok')
        pipe_response(pipe, 'ucinewgame')
        ans = [analyze_position(pipe, None, opt['level'])]
        for halfmove_num in range(len(game)):
            moves = ' '.join(game[:halfmove_num + 1])
            ans.append(analyze_position(pipe, moves, opt['level']))
        if ans[-1][0] == 'mate' and ans[-1][1] == '0':
            del(ans[-1])
        pipe_response(pipe, 'quit')
        return ans
    return None


def analyze_position(pipe, moves, level):
    pipe_response(pipe, 'isready', 'readyok')
    pipe_response(pipe, 'position startpos moves ' + moves if moves else
                  'position startpos')
    pipe_response(pipe, 'isready', 'readyok')
    out = pipe_response(pipe, 'go ' + level, 'bestmove')
    return analysis_result(out)


def get_stats(headers, result, opt):
    ans = {}
    for hdr, res in zip(headers, result):
        for side in ('White', 'Black'):
            stat = get_stat(res, side, opt)
            if not stat:
                continue
            if hdr[side] not in ans:
                ans[hdr[side]] = stat
            else:
                ans[hdr[side]] = update_stat(ans[hdr[side]], stat)
    return ans


def get_score(pair):
    if pair[0] == 'cp':
        return int(pair[1])
    return 32000 if pair[1][0] != '-' else -32000


def get_stat(result, side, opt):
    sum_cp_loss = 0
    ans = {'avg_cp_loss': 0, 'inaccuracies': 0, 'mistakes': 0,
           'blunders': 0, 'mate_blunders': 0, 'moves': 0, 'games': 1}
    first = int(opt['skip_first_moves']) if opt['skip_first_moves'] else 0
    evals = get_list_of_lists(result, side, first)
    if not evals or len(evals) == 0:
        return None
    for e in evals:
        cp1 = get_score(e[0])
        cp2 = -get_score(e[1])
        cp_loss = cp1 - cp2 if cp2 < cp1 else 0
        if cp_loss >= 16000:
            ans['mate_blunders'] += 1
            cp_loss = 0
        sum_cp_loss += cp_loss
        if cp_loss >= int(opt['blunder']):
            ans['blunders'] += 1
        elif cp_loss >= int(opt['mistake']):
            ans['mistakes'] += 1
        elif cp_loss >= int(opt['inaccuracy']):
            ans['inaccuracies'] += 1
    ans['moves'] = len(evals)
    ans['avg_cp_loss'] = sum_cp_loss/len(evals)
    return ans


def get_list_of_lists(result, side, first):
    ans1 = result[2*first:]
    if not ans1:
        return None
    if side == 'Black':
        del(ans1[0])
    ans2 = [ans1[i:i + 2] for i in range(0, len(ans1), 2)]
    if ans2 and len(ans2[-1]) == 1:
        del(ans2[-1])

    return ans2


def update_stat(old, new):
    acl, ms = 'avg_cp_loss', 'moves'
    avg_cp_loss = (old[acl]*old[ms] + new[acl]*new[ms])/(old[ms] + new[ms])
    new = {k: old[k] + new[k] for k in old}
    new[acl] = avg_cp_loss
    return new


def out_stats(stats, player_name):
    ans = sorted(stats.items(), key=lambda it: it[1]['games'], reverse=True)
    if player_name:
        ans = {k: v for k, v in ans.items() if player_name in k.lower()}
    for i, a in enumerate(ans):
        print(f'{i + 1}. {a[0]}. Games: {a[1]["games"]}. Moves: '
              f'{a[1]["moves"]}. Mate blunders: {a[1]["mate_blunders"]}. '
              f'Blunders: {a[1]["blunders"]}. Mistakes: {a[1]["mistakes"]}. '
              f'Inaccuracies: {a[1]["inaccuracies"]}. Average loss: '
              f'{a[1]["avg_cp_loss"]: .1f} centipawns'
              )


def pgn_to_uci(opt):
    uci_games = []
    headers = []
    game_cr = 0
    first, last = opt['first_game'], opt['last_game']
    player = opt['only_if_player_name_contains'].lower()
    if not first or not last or int(first) <= 0 or int(last) <= 0:
        first, last = 1, int(1e9)
    else:
        first, last = int(first), int(last)
    with open(opt['pgn_input']) as file:
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
            tmp = [x.split('/')[0] for x in line.split() if '/' in x
                   and x != '1/2-1/2']
            ans += [['cp', str(int(float(x)*100))] if 'M' not in x else
                    ['mate', x[0] + x[2:]]for x in tmp]
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


def test():
    opt = {"first_game": "",
           "last_game": "",
           "skip_first_moves": "",
           "only_if_player_name_contains": "",
           "inaccuracy": "50",
           "mistake": "100",
           "blunder": "300"}
    results = get_values_from_pgn('test_games.pgn', '', '')
    headers = 2*[{'White': 'Player1', 'Black': 'Player2'}]
    stats = get_stats(headers, results, opt)
    assert stats == {'Player1': {'avg_cp_loss': 215.0,
                                 'inaccuracies': 1,
                                 'mistakes': 0,
                                 'blunders': 1,
                                 'mate_blunders': 2,
                                 'moves': 6,
                                 'games': 2},
                     'Player2': {'avg_cp_loss': 244.0,
                                 'inaccuracies': 0,
                                 'mistakes': 1,
                                 'blunders': 1,
                                 'mate_blunders': 1,
                                 'moves': 5,
                                 'games': 2}}


if __name__ == '__main__':
    test()
    main()
