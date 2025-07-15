import subprocess
from PyQt6.QtCore import QThread, pyqtSignal, QObject

class FFmpegWorker(QThread):
    progress = pyqtSignal(int)
    log      = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, commands):
        super().__init__()
        self.commands = commands
        self._cancel = False
        self._proc = None

    def run(self):
        total = len(self.commands)
        for idx, cmd in enumerate(self.commands, start=1):
            if self._cancel:
                self.log.emit("⛔️ Taak geannuleerd")
                self.finished.emit(False, "")
                return
            self.log.emit(f"▶️ {cmd}")
            try:
                self._proc = subprocess.Popen(
                    cmd, shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                while True:
                    if self._cancel and self._proc:
                        self._proc.terminate()
                        self.log.emit("⛔️ FFmpeg proces afgebroken.")
                        self.finished.emit(False, "")
                        return
                    line = self._proc.stderr.readline()
                    if not line:
                        break
                    self.log.emit(line.rstrip())
                self._proc.wait()
            except Exception as e:
                self.log.emit(f"❌ Fout in worker: {e}")
                self.finished.emit(False, "")
                return
            finally:
                self._proc = None

            if self._cancel:
                self.log.emit("⛔️ Taak geannuleerd tijdens wachten.")
                self.finished.emit(False, "")
                return
            if self._proc and self._proc.returncode != 0:
                self.log.emit(f"❌ Fout bij stap {idx}, code {self._proc.returncode}")
                self.finished.emit(False, "")
                return
            pct = int(idx/total * 100)
            self.progress.emit(pct)

        self.log.emit("✅ Alle stappen voltooid")
        self.finished.emit(True, self.commands[-1])

    def cancel(self):
        self._cancel = True
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass

class FFmpegWorkerManager(QObject):
    def __init__(self):
        super().__init__()
        self._active_worker = None

    def start_worker(self, cmds, progress_cb, log_cb, finished_cb):
        if self._active_worker:
            self._active_worker.cancel()
        worker = FFmpegWorker(cmds)
        worker.progress.connect(progress_cb)
        worker.log.connect(log_cb)
        worker.finished.connect(finished_cb)
        self._active_worker = worker
        worker.start()
        return worker

    def cancel(self):
        if self._active_worker:
            self._active_worker.cancel()
            self._active_worker = None
