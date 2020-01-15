from .error_message import *
from .model_decorator import RecordFieldEditor, RecordFieldExtend, RecordFieldFilter
from datetime import datetime
from .i18n import *


class RecordField:
    def __init__(self, field_name, parameter_name=None, default=None, required=True):
        self.field_name = field_name
        if parameter_name is None:
            parameter_name = field_name
        self.parameter_name = parameter_name
        self.default = default
        self.required = required

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

        setattr(record, self.field_name, value)

    def record_value(self, record):
        try:
            value = RecordFieldExtend.record_value(record, self.field_name)
        except Exception as e:
            if isinstance(e, CustomHTTPError):
                raise e
            else:
                raise parameter_error(str(e))
        if value is not None:
            return value

        if hasattr(record, self.field_name):
            value = getattr(record, self.field_name)

        return value


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


class RecordInFilter(RecordFilter):
    def filter_query(self, request, query, request_header=None):
        filter_value = self.request_value(request)
        if filter_value is None or (isinstance(filter_value, str) and len(filter_value) == 0):
            if self.required:
                raise parameter_error(i18n(PARAMETER_NOT_EXIST_ERROR).format(self.parameter_name))
            return query

        filter_value = filter_value.split(',')
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
