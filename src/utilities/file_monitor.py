import os
from twisted.internet import reactor
from twisted.internet.task import deferLater


class FileMonitor:
    mod_times = {}
    src_path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    monitor_dir = os.path.join(src_path, 'src', 'monitored_files', 'ians_share')

    def __init__(self, slave):
        print("FILE CHANGE MONITOR: Started")
        self.slave = slave
        self.start_monitor()

    def start_monitor(self):
        # Check all files for changes
        for file in os.listdir(self.monitor_dir):
            file_path = os.path.join(self.monitor_dir, file)

            # Check files for recent mod time stamps
            if file in self.mod_times:
                last_mod_time = self.mod_times[file]
                new_mod_time = os.path.getmtime(file_path)
                time_since_update = new_mod_time - last_mod_time
                self.mod_times[file] = new_mod_time

                # Initiate update for altered files
                if time_since_update > 0:
                    self.slave.file_changed(file, new_mod_time)
            else:
                self.mod_times[file] = os.path.getmtime(file_path)

        deferLater(reactor, 3, self.start_monitor)


if __name__ == '__main__':
    FileMonitor()