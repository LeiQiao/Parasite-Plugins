import pa
from time import sleep
from datetime import datetime, timedelta
import re


class Schedule:
    def __init__(self):
        self.time = None
        self.schedule_id = None
        self.next_runtime = None

    def start(self, schedule_time, schedule_id):
        self.time = schedule_time
        self.schedule_id = schedule_id
        self._calc_next_runtime()

    # Overridable -- first_run
    def first_run(self):
        self.run()

    # Overridable -- run
    def run(self):
        pass

    def sleep(self):
        timeinterval = (self.next_runtime - datetime.now()).total_seconds()
        if timeinterval < 0:
            pa.log.warning('schedule {0} delay {1}ms'.format(self.schedule_id, -int(timeinterval*1000)))
        else:
            pa.log.debug('schedule {0} sleep, wake up at {1}'.format(self.schedule_id, self.next_runtime))
            sleep(timeinterval)
        self._calc_next_runtime()

    def _calc_next_runtime(self):
        next_runtime = datetime.now()
        next_runtime += timedelta(0, 1, -next_runtime.microsecond)
        time_segments = self.time.split(' ')
        if len(time_segments) != 6:
            raise SyntaxError('schedule {0} time format error: {1}'.format(self.schedule_id, self.time))

        try:
            seconds = self._calc_next_possible_value(syntax=time_segments[0],
                                                     value=next_runtime.second,
                                                     value_range=(0, 59))
        except Exception as e:
            raise SyntaxError('schedule {0} second {1}'.format(self.schedule_id, str(e)))
        next_runtime += timedelta(seconds=seconds)

        try:
            minutes = self._calc_next_possible_value(syntax=time_segments[1],
                                                     value=next_runtime.minute,
                                                     value_range=(0, 59))
        except Exception as e:
            raise SyntaxError('schedule {0} minute {1}'.format(self.schedule_id, str(e)))
        next_runtime += timedelta(minutes=minutes)

        try:
            hours = self._calc_next_possible_value(syntax=time_segments[2],
                                                   value=next_runtime.hour,
                                                   value_range=(0, 23))
        except Exception as e:
            raise SyntaxError('schedule {0} hour {1}'.format(self.schedule_id, str(e)))
        next_runtime += timedelta(hours=hours)

        try:
            days = self._calc_next_possible_value(syntax=time_segments[3],
                                                  value=next_runtime.day,
                                                  value_range=(1, 31))
        except Exception as e:
            raise SyntaxError('schedule {0} day {1}'.format(self.schedule_id, str(e)))
        next_runtime += timedelta(days=days)

        try:
            months = self._calc_next_possible_value(syntax=time_segments[4],
                                                    value=next_runtime.month,
                                                    value_range=(1, 12))
        except Exception as e:
            raise SyntaxError('schedule {0} month {1}'.format(self.schedule_id, str(e)))
        next_runtime = self._add_month(next_runtime, months)

        try:
            days = self._calc_next_possible_value(syntax=time_segments[5],
                                                  value=next_runtime.weekday(),
                                                  value_range=(0, 6))
        except Exception as e:
            raise SyntaxError('schedule {0} week {1}'.format(self.schedule_id, str(e)))
        next_runtime += timedelta(days=days)

        self.next_runtime = next_runtime

    @staticmethod
    def _calc_next_possible_value(syntax, value, value_range):
        if syntax == '*':
            return 0

        allow_values = set()
        segments = syntax.split(',')
        for seg in segments:
            if re.match('^\d+$', seg):
                # parse for pure digit
                if int(seg) < value_range[0] or int(seg) > value_range[1]:
                    raise SyntaxError('value {0} not between in {1}-{2}'.format(seg, value_range[0], value_range[1]))
                allow_values.add(int(seg))
            elif re.match('^(\d+)-(\d+)$', seg):
                # parse for x-y
                matches = re.match('^(\d+)-(\d+)$', seg)
                start = int(matches.group(1))
                end = int(matches.group(2))
                if start < value_range[0] or start > value_range[1]:
                    raise SyntaxError('value {0} not between in {1}-{2}'.format(start, value_range[0], value_range[1]))
                if end < value_range[0] or end > value_range[1]:
                    raise SyntaxError('value {0} not between in {1}-{2}'.format(end, value_range[0], value_range[1]))
                if start > end:
                    for i in range(start, value_range[1]+1):
                        allow_values.add(i)
                    for i in range(value_range[0], end+1):
                        allow_values.add(i)
                else:
                    for i in range(start, end+1):
                        allow_values.add(i)
            elif re.match('^[*][/](\d+)$', seg):
                # parse for */x
                matches = re.match('^\*/(\d+)$', seg)
                d = int(matches.group(1))
                for i in range(value_range[0], value_range[1]+1):
                    if i % d == 0:
                        allow_values.add(i)
        # 转换成 list 并排序
        allow_values = list(allow_values)
        allow_values.sort()

        # 如果给定的值在允许的范围内
        if value in allow_values:
            return 0

        # 如果给定的值大于最后一个允许的值，计算进入最小允许值的步长
        last_value = allow_values[len(allow_values)-1]
        if value > last_value:
            return value_range[1] - last_value + (allow_values[0] - value_range[0])

        # 计算给定的值到下一个允许值的步长
        for i in allow_values:
            if i > value:
                return i - value

        return 0

    @staticmethod
    def _add_month(time, months):
        month = time.month + months
        year = time.year
        while month > 12:
            year += 1
            month -= 12
        return datetime(year=year, month=month, day=time.day, hour=time.hour, minute=time.minute, second=time.second)
