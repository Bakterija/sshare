#!/usr/bin/env python3
from time import sleep, time
from queue import Queue, Empty
from threading import Thread
from logs import Logger
import subprocess
import utils
import os


class HotLoader(object):
    P_NOT_STARTED = 1
    P_STOPPED = 2
    P_CRASHED = 3
    P_RUNNING = 4
    TIME0 = time()

    sleep_timer = 1
    process_state = P_NOT_STARTED
    restarted_times = 0
    process = None
    process_log = []
    _queue = Queue()
    print_output = True
    monitor_paths = []
    cmd = []

    def __init__(self, **kwargs):
        TIME0 = time()
        self.write_log('init')
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def timer(self):
        return round(time() - self.TIME0, 2)

    def write_log(self, message, level='info'):
        if level[0] == 'i':
            Logger.info('HotLoader: %s %s' % (self.timer, message))
        elif level[0] == 'e':
            Logger.error('HotLoader: %s %s' % (self.timer, message))

    def _start_subprocess(self, cmd):
        popen = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT, universal_newlines=False)
        self.process = popen

        for stdout_line in iter(popen.stdout.readline, ""):
            if stdout_line:
                text = stdout_line.decode('utf-8').rstrip()
                self._queue.put(text)
            else:
                break
        self.process = None
        popen.stdout.close()
        popen.stdin.close()
        return_code = popen.wait()
        if return_code:
            if return_code == -9:
                pass
            else:
                raise subprocess.CalledProcessError(return_code, cmd)

    def _start_process(self):
        try:
            self.write_log('start_process')
            self.process_state = self.P_RUNNING
            self._start_subprocess(self.cmd)
            self.write_log('process exited')
            self.process_state = self.P_STOPPED
        except:
            self.write_log('process crashed', level='error')
            self.process_state = self.P_CRASHED

    def _stop_process(self):
        if self.process:
            self.process.kill()

    def _get_queued_messages(self):
        try:
            for i in range(100):
                t = self._queue.get_nowait()
                self.process_log.append(t)
                if self.print_output:
                    print(t)
        except Empty:
            pass

    def start(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        last_modification_time = os.path.getmtime(dir_path)
        try:
            while True:
                self._get_queued_messages()
                if self.process_state != self.P_RUNNING:
                    self.restarted_times += 1
                    if self.process_state in (self.P_STOPPED, self.P_CRASHED):
                        if self.restarted_times is 0:
                            tt = 'HotLoader: %s restarting process' % (
                                self.timer)
                        else:
                            tt = 'HotLoader: %s restarting process (%s)' % (
                                self.timer, self.restarted_times)
                        Logger.info(tt)
                    if self.process_state == self.P_CRASHED:
                        sleep(self.sleep_timer)
                    self.process_state = self.P_RUNNING
                    t = Thread(target=self._start_process)
                    t.start()
                    sleep(self.sleep_timer)

                new_modification_time = os.path.getmtime(dir_path)
                for x in self.monitor_paths:
                    try:
                        mod = os.path.getmtime(x)
                        if mod > new_modification_time:
                            new_modification_time = mod
                    except FileNotFoundError:
                        pass

                if new_modification_time > last_modification_time:
                    self.write_log('new modifications')
                    last_modification_time = new_modification_time + 1.0
                    if self.P_RUNNING:
                        self._stop_process()
                sleep(self.sleep_timer)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    monitor_paths = utils.get_files(dir_path)
    hotloader = HotLoader(
        cmd=["python3", "-u", "main.py"],
        monitor_paths=monitor_paths
        ).start()
