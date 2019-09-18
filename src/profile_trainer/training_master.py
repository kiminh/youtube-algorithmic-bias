import datetime
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor as Pool

import settings


def run_command(cmd):
    # Shell need to set to true
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')


def main():
    # Name list extracted from path, to name log file
    names = [path.split('/')[-1].split('_')[-1].split('.json')[0] for path in settings.training_list]
    # Seed cookies, list of path
    scl = settings.seed_cookies_list
    # After training cookies, list of path
    tcl = settings.training_cookies_list
    # Video for training json files, list of path
    tl = settings.training_list
    # Useful in virtual environment to run through specific interpreter
    # abs_p = os.getcwd()
    log = settings.log_root_path
    # For current project, assume each training list corrsponds to one cookie/profile
    if len(scl) != len(tcl) or len(tcl) != len(tl):
        raise Exception('names list, cookies dimentions not match')
    cmds = []
    today = str(datetime.datetime.now().strftime('%Y-%b-%d-%H-%M'))
    log_path = os.path.join(settings.log_root_path, today + '-log')
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    for n, sc, tc, t in zip(names, scl, tcl, tl):
        cmd = f'nohup {sys.executable} training.py ' + \
            f'--path {t} ' + \
            f'--sc {sc} ' + \
            f'--tc {tc} ' + \
            f'> {os.path.join(log_path, n)}.log &'
        print(f'Command for {n}: {cmd}')
        cmds.append(cmd)
    print(f'\nMaster training starts, current time: {time.ctime()}')
    print(f'log path: {log_path}')
    with Pool(max_workers=len(cmds)) as pool:
        pool.map(run_command, cmds)
    print(f'\nMaster training ends, current time: {time.ctime()}')


if __name__ == '__main__':
    if settings.master_mode:
        main()
        time.sleep(60)
        # Seen leftover firefox processes after finish running normally
        # Linux uses fork to create new processes, os._exit() will kill such processes.
        os._exit(0)
    else:
        raise Exception('Not in master training mode')
