from multiprocessing import Process, Queue
from .locker import FileLocker
from .schedule import Schedule
import pa
from datetime import datetime


def worker_process(schedule_id, work_class, schedule_time):
    # 这里需要使用 __name__ 进行比较
    if work_class.__base__.__name__ != Schedule.__name__:
        raise ImportError('schedule class \'{0}\' is not a subclass of \'Schedule\''.format(work_class))

    schedule = work_class()
    schedule.start(schedule_time, schedule_id)

    first_run = True
    while True:
        try:
            schedule.run_times += 1
            pa.log.debug('schedule {0} triggered at {1}, {2} times'
                         .format(schedule.schedule_id, datetime.now(), schedule.run_times))
            if first_run:
                first_run = False
                schedule.first_run()
            else:
                schedule.run()
        except Exception as e:
            pa.log.error('schedule {0} error: {1}'.format(schedule.schedule_id, e))

        schedule.sleep()


class ScheduleGuardian(Process):
    locker = FileLocker()

    def __init__(self):
        super(ScheduleGuardian, self).__init__()
        self.queue = Queue()
        self.jobs = []

    def regist_schedule_job(self, schedule_id, class_name, schedule_time):
        self.queue.put({
            'schedule_id': schedule_id,
            'class_name': class_name,
            'schedule_time': schedule_time
        })

    def run(self):
        if not self.locker.lock():
            pa.log.info('base_schedule already running. exit')
            exit(0)

        pa.log.info('base_schedule guardain start')

        while True:
            value = self.queue.get()
            if value is None or \
               'schedule_id' not in value or \
               'class_name'not in value or \
               'schedule_time' not in value:
                continue

            job_process = Process(target=worker_process,
                                  args=(value['schedule_id'], value['class_name'], value['schedule_time']))
            job_process.start()
            self.jobs.append(job_process)
