import fcntl


class FileLocker:
    def __init__(self):
        self.file_handler = None

    def lock(self, file_path='/var/tmp/pa_schedule.lock'):
        self.file_handler = open(file_path, 'w')
        try:
            fcntl.lockf(self.file_handler, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except Exception as e:
            str(e)
            return False
