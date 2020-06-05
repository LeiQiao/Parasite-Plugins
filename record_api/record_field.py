from .error_message import *
from .model_decorator import RecordFieldEditor, RecordFieldExtend, RecordFieldFilter
from datetime import datetime
from .i18n import *
from .model_decorator import ExtraColumn


class RecordField:
    def __init__(self, field_name, parameter_name=None, default=None, required=True, formatter=None):
        self.field_name = field_name
        if parameter_name is None:
            parameter_name = field_name
        self.parameter_name = parameter_name
        self.default = default
        self.required = required
        self.formatter = formatter

    def has_value(self, request):
        if self.parameter_name in request:
            return True
        if self.default is not None:
            return True
        return False

    def request_value(self, request):
        if request is not None and self.parameter_name in request:
            return request[self.parameter_name]
        elif self.default is not None:
            if callable(self.default):
                return self.default()
            else:
                return self.default
        else:
            return None

    def set_value(self, request, record):
        value = self.request_value(request)
        if value is None:
            if self.required:
                raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.parameter_name))
            return

        try:
            if RecordFieldEditor.onchange(record, self.field_name, value):
                return
        except Exception as e:
            if isinstance(e, CustomHTTPError):
                raise e
            else:
                raise parameter_error(str(e))

        if not hasattr(record, self.field_name):
            raise record_field_not_found_error(i18n(FIELD_NOT_EXIST_ERROR)
                                               .format(record.__class__.__name__, self.field_name))

        if self.formatter is not None and callable(self.formatter):
            value = self.formatter(value)

        setattr(record, self.field_name, self.format_value(value))

    def record_value(self, record):
        try:
            value = RecordFieldExtend.record_value(record, self.field_name)
        except Exception as e:
            if isinstance(e, CustomHTTPError):
                raise e
            else:
                raise parameter_error(str(e))
        if value is not None:
            return self.format_value(value)

        if isinstance(record, tuple):
            for rcd in record:
                if self.has_record_attr(rcd, self.field_name):
                    value = self.get_attr_from_record(rcd, self.field_name)
                    if value is not None:
                        return self.format_value(value)
                    else:
                        return self.default

        if self.has_record_attr(record, self.field_name):
            value = self.format_value(self.get_attr_from_record(record, self.field_name))

        if value is None:
            if callable(self.default):
                value = self.format_value(self.default())
            else:
                value = self.default
        return value

    def format_value(self, value):
        if self.formatter is None or not callable(self.formatter):
            return value
        return self.formatter(value)

    @staticmethod
    def has_record_attr(record, attr_name):
        attrs = attr_name.split('.')
        if len(attrs) == 0:
            return hasattr(record, attr_name)

        rcd = record
        for attr in attrs:
            if hasattr(rcd, attr):
                rcd = getattr(rcd, attr)
            else:
                return False
        return True

    @staticmethod
    def get_attr_from_record(record, attr_name):
        attrs = attr_name.split('.')

        rcd = record
        for attr in attrs:
            if hasattr(rcd, attr):
                rcd = getattr(rcd, attr)
            else:
                return None

        if isinstance(rcd, ExtraColumn):
            return rcd.default
        return rcd


class JoinedRecordField(RecordField):
    def __init__(self, field_name, parameter_name=None, default=None, required=True, formatter=None):
        # 默认为分段的最后一个参数，例如获取设备 ID，field_name 为 Device.id 则默认的 parameter_name 为 id
        if parameter_name is None:
            parameter_name = field_name.split('.')[-1]

        super(JoinedRecordField, self).__init__(field_name, parameter_name, default, required, formatter)


class RecordFilter(RecordField):
    def filter_query(self, request, query, request_header=None):
        filter_value = self.request_value(request)
        if filter_value is None or (isinstance(filter_value, str) and len(filter_value) == 0):
            if self.required:
                raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.parameter_name))
            return query

        try:
            model_filter = RecordFieldFilter.filter_query(query, self.field_name, request, request_header)
            if model_filter is not None:
                return model_filter
        except Exception as e:
            if isinstance(e, CustomHTTPError):
                raise e
            else:
                raise parameter_error(str(e))

        return query.filter(getattr(RecordFieldFilter.model_class(query), self.field_name) == filter_value)


class RecordCompareFilter(RecordFilter):
    Equal = 1
    Less = 2
    EqualAndLess = 3
    Great = 4
    EqualAndGreat = 5
    NotEqual = 6

    def __init__(self, field_name, parameter_name=None, default=None, required=True, compare_op=Equal):
        super(RecordCompareFilter, self).__init__(field_name, parameter_name, default, required)
        self.compare_op = compare_op

    def filter_query(self, request, query, request_header=None):
        filter_value = self.request_value(request)
        if filter_value is None or (isinstance(filter_value, str) and len(filter_value) == 0):
            if self.required:
                raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.parameter_name))
            return query

        if isinstance(filter_value, str):
            filter_value = filter_value.split(',')
        q = getattr(RecordFieldFilter.model_class(query), self.field_name)
        if self.compare_op == RecordCompareFilter.Equal:
            q = (q == filter_value)
        elif self.compare_op == RecordCompareFilter.NotEqual:
            q = (q != filter_value)
        elif self.compare_op == RecordCompareFilter.Less:
            q = (q < filter_value)
        elif self.compare_op == RecordCompareFilter.EqualAndLess:
            q = (q <= filter_value)
        elif self.compare_op == RecordCompareFilter.Great:
            q = (q > filter_value)
        elif self.compare_op == RecordCompareFilter.EqualAndGreat:
            q = (q >= filter_value)
        return query.filter(q)


class RecordInFilter(RecordFilter):
    def filter_query(self, request, query, request_header=None):
        filter_value = self.request_value(request)
        if filter_value is None or (isinstance(filter_value, str) and len(filter_value) == 0):
            if self.required:
                raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.parameter_name))
            return query

        filter_value = filter_value.split(',')
        filter_value = [x for x in filter_value if x]
        return query.filter(getattr(RecordFieldFilter.model_class(query), self.field_name).in_(filter_value))


class RecordLikeFilter(RecordFilter):
    def filter_query(self, request, query, request_header=None):
        filter_value = self.request_value(request)
        if filter_value is None or (isinstance(filter_value, str) and len(filter_value) == 0):
            if self.required:
                raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.parameter_name))
            return query

        return query.filter(getattr(RecordFieldFilter.model_class(query), self.field_name)
                            .like('%{0}%'.format(filter_value)))


class RecordRangeFilter(RecordFilter):
    def __init__(self, field_name, range_start_parameter_name, range_end_parameter_name,
                 start_required=True, end_required=True):
        super(RecordRangeFilter, self).__init__(field_name, required=False)
        self.parameter_name = None
        self.range_start_parameter_name = range_start_parameter_name
        self.range_end_parameter_name = range_end_parameter_name
        self.start_required = start_required
        self.end_required = end_required

    def check_value_format(self, value):
        return True

    def filter_query(self, request, query, request_header=None):
        if self.range_start_parameter_name in request:
            filter_start_value = request[self.range_start_parameter_name]
        else:
            filter_start_value = None

        if self.range_end_parameter_name in request:
            filter_end_value = request[self.range_end_parameter_name]
        else:
            filter_end_value = None

        if (filter_start_value is None or (isinstance(filter_start_value, str) and len(filter_start_value) == 0)) \
                and self.start_required:
            raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.range_start_parameter_name))

        if (filter_end_value is None or (isinstance(filter_start_value, str) and len(filter_end_value) == 0)) \
                and self.end_required:
            raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.range_end_parameter_name))

        if filter_start_value is not None and \
                ((not isinstance(filter_start_value, str)) or len(filter_start_value) > 0):
            if not self.check_value_format(filter_start_value):
                raise parameter_error(i18n(PARAMETER_FORMAT_ERROR).format(self.range_start_parameter_name))
            # if filter_start_value.isdigit():
            #     filter_start_value = int(filter_start_value)
            query = query.filter(getattr(RecordFieldFilter.model_class(query), self.field_name) >= filter_start_value)
        if filter_end_value is not None and \
                ((not isinstance(filter_end_value, str)) or len(filter_end_value) > 0):
            if not self.check_value_format(filter_start_value):
                raise parameter_error(i18n(PARAMETER_FORMAT_ERROR).format(self.range_end_parameter_name))
            # if filter_end_value.isdigit():
            #     filter_end_value = int(filter_end_value)
            query = query.filter(getattr(RecordFieldFilter.model_class(query), self.field_name) <= filter_end_value)

        return query


class RecordDateRangeFilter(RecordRangeFilter):
    def check_value_format(self, value):
        date_patterns = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
        for pattern in date_patterns:
            try:
                datetime.strptime(value, pattern).date()
                return True
            except Exception as e:
                str(e)
                pass
        return False
