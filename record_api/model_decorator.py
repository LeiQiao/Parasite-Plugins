# noinspection PyPep8Naming
class ri:
    @staticmethod
    def get_class_name_from_function(func):
        return func.__qualname__.split('.')[-2]

    @staticmethod
    def onchange(*args):
        def decorated(func):
            RecordFieldEditor.add_editor(ri.get_class_name_from_function(func), args, func)
            return func

        return decorated

    @staticmethod
    def onflush():
        def decorated(func):
            RecordFieldEditor.add_flush(ri.get_class_name_from_function(func), func)
            return func
        return decorated

    @staticmethod
    def endflush():
        def decorated(func):
            RecordFieldEditor.add_end_flush(ri.get_class_name_from_function(func), func)
            return func
        return decorated

    @staticmethod
    def endadd():
        def decorated(func):
            RecordFieldEditor.add_end_add(ri.get_class_name_from_function(func), func)
            return func
        return decorated

    @staticmethod
    def ondelete():
        def decorated(func):
            RecordFieldEditor.add_delete(ri.get_class_name_from_function(func), func)
            return func
        return decorated

    @staticmethod
    def enddelete():
        def decorated(func):
            RecordFieldEditor.add_end_delete(ri.get_class_name_from_function(func), func)
        return decorated

    @staticmethod
    def field(field_name):
        def decorated(func):
            RecordFieldExtend.add_field(ri.get_class_name_from_function(func), field_name, func)
            return func

        return decorated

    @staticmethod
    def filter(filter_name):
        def decorated(func):
            RecordFieldFilter.add_filter(ri.get_class_name_from_function(func), filter_name, func)
            return func

        return decorated

    @staticmethod
    def foreign_onflush(foreign_model):
        def decorated(func):
            RecordFieldEditor.add_flush(foreign_model.__name__, func)
            return func
        return decorated

    @staticmethod
    def foreign_endflush(foreign_model):
        def decorated(func):
            RecordFieldEditor.add_end_flush(foreign_model.__name__, func)
            return func
        return decorated

    @staticmethod
    def foreign_endadd(foreign_model):
        def decorated(func):
            RecordFieldEditor.add_end_add(foreign_model.__name__, func)
            return func
        return decorated

    @staticmethod
    def foreign_ondelete(foreign_model):
        def decorated(func):
            RecordFieldEditor.add_delete(foreign_model.__name__, func)
            return func
        return decorated

    @staticmethod
    def foreign_enddelete(foreign_model):
        def decorated(func):
            RecordFieldEditor.add_end_delete(foreign_model.__name__, func)
            return func
        return decorated


class RecordFieldEditor:
    _all_record_field = []
    _all_record_flush = {}
    _all_record_end_flush = {}
    _all_record_end_add = {}
    _all_record_delete = {}
    _all_record_end_delete = {}
    _field_value_wait_for_flush = {}

    def __init__(self, model_name, field_names, func):
        self.model_name = model_name
        self.field_names = field_names
        self.func = func
        self._all_record_field.append(self)

    @staticmethod
    def add_editor(model_name, field_names, func):
        RecordFieldEditor(model_name, field_names, func)

    @staticmethod
    def add_flush(model_name, func):
        funcs = []
        if model_name in RecordFieldEditor._all_record_flush:
            funcs = RecordFieldEditor._all_record_flush[model_name]
        funcs.append(func)
        RecordFieldEditor._all_record_flush[model_name] = funcs

    @staticmethod
    def add_end_flush(model_name, func):
        funcs = []
        if model_name in RecordFieldEditor._all_record_end_flush:
            funcs = RecordFieldEditor._all_record_end_flush[model_name]
        funcs.append(func)
        RecordFieldEditor._all_record_end_flush[model_name] = funcs

    @staticmethod
    def add_end_add(model_name, func):
        funcs = []
        if model_name in RecordFieldEditor._all_record_end_add:
            funcs = RecordFieldEditor._all_record_end_add[model_name]
        funcs.append(func)
        RecordFieldEditor._all_record_end_add[model_name] = funcs

    @staticmethod
    def add_delete(model_name, func):
        funcs = []
        if model_name in RecordFieldEditor._all_record_delete:
            funcs = RecordFieldEditor._all_record_delete[model_name]
        funcs.append(func)
        RecordFieldEditor._all_record_delete[model_name] = funcs

    @staticmethod
    def add_end_delete(model_name, func):
        funcs = []
        if model_name in RecordFieldEditor._all_record_end_delete:
            funcs = RecordFieldEditor._all_record_end_delete[model_name]
        funcs.append(func)
        RecordFieldEditor._all_record_end_delete[model_name] = funcs

    @staticmethod
    def onchange(record, field_name, value):
        for record_field in RecordFieldEditor._all_record_field:
            if record_field.model_name == record.__class__.__name__ and \
                    field_name in record_field.field_names:

                # 当前记录的所有 onchange 事件
                record_wait_for_flush = {}
                if record in RecordFieldEditor._field_value_wait_for_flush:
                    record_wait_for_flush = RecordFieldEditor._field_value_wait_for_flush[record]
                    if record_field not in record_wait_for_flush:
                        record_wait_for_flush[record_field] = {}
                else:
                    record_wait_for_flush[record_field] = {}
                    RecordFieldEditor._field_value_wait_for_flush[record] = record_wait_for_flush

                # 缓存当前记录的当前 onchange 事件的当前字段名
                record_wait_for_flush[record_field][field_name] = value

                # 判断当前记录的当前 onchange 事件的所有字段是否已经被写入缓存
                flush_fields = []
                for fname in record_field.field_names:
                    if fname in record_wait_for_flush[record_field]:
                        flush_fields.append(record_wait_for_flush[record_field][fname])
                    else:
                        flush_fields = None
                        break

                # 调用当前记录的当前 onchange 事件，并将参数传递到 onchange 方法, 并删除当前 onchange 事件的缓存
                if flush_fields is not None:
                    try:
                        record_field.func(record, *flush_fields)
                    except Exception as e:
                        del RecordFieldEditor._field_value_wait_for_flush[record]
                        raise e
                    del record_wait_for_flush[record_field]

                # 如果当前记录的所有 onchange 事件都结束
                if len(record_wait_for_flush.keys()) == 0:
                    del RecordFieldEditor._field_value_wait_for_flush[record]

                # 已处理
                return True
        # 未处理
        return False

    @staticmethod
    def flush(record):
        if record not in RecordFieldEditor._field_value_wait_for_flush:
            # invoke onflush
            if record.__class__.__name__ in RecordFieldEditor._all_record_flush:
                funcs = RecordFieldEditor._all_record_flush[record.__class__.__name__]
                for func in funcs:
                    func(record)
            return
        record_wait_for_flush = RecordFieldEditor._field_value_wait_for_flush[record]
        for record_field in record_wait_for_flush:
            flush_fields = []
            for fname in record_field.field_names:
                if fname in record_wait_for_flush[record_field]:
                    flush_fields.append(record_wait_for_flush[record_field][fname])
                else:
                    flush_fields.append(getattr(record, fname))

            # 调用当前记录的当前 onchange 事件，并将参数传递到 onchange 方法, 并删除当前 onchange 事件的缓存
            if flush_fields is not None:
                try:
                    record_field.func(record, *flush_fields)
                except Exception as e:
                    del RecordFieldEditor._field_value_wait_for_flush[record]
                    raise e
        del RecordFieldEditor._field_value_wait_for_flush[record]
        # invoke onflush
        if record.__class__.__name__ in RecordFieldEditor._all_record_flush:
            funcs = RecordFieldEditor._all_record_flush[record.__class__.__name__]
            for func in funcs:
                func(record)

    @staticmethod
    def endflush(record):
        # invoke endflush
        if record.__class__.__name__ in RecordFieldEditor._all_record_end_flush:
            funcs = RecordFieldEditor._all_record_end_flush[record.__class__.__name__]
            for func in funcs:
                func(record)

    @staticmethod
    def endadd(record):
        # invoke endadd
        if record.__class__.__name__ in RecordFieldEditor._all_record_end_add:
            funcs = RecordFieldEditor._all_record_end_add[record.__class__.__name__]
            for func in funcs:
                func(record)

    @staticmethod
    def delete(record):
        # invoke ondelete
        if record.__class__.__name__ in RecordFieldEditor._all_record_delete:
            funcs = RecordFieldEditor._all_record_delete[record.__class__.__name__]
            for func in funcs:
                func(record)

    @staticmethod
    def enddelete(record):
        # invoke enddelete
        if record.__class__.__name__ in RecordFieldEditor._all_record_end_delete:
            funcs = RecordFieldEditor._all_record_end_delete[record.__class__.__name__]
            for func in funcs:
                func(record)


class RecordFieldExtend:
    _all_record_field = []

    def __init__(self, model_name, field_name, func):
        self.model_name = model_name
        self.field_name = field_name
        self.func = func
        self._all_record_field.append(self)

    @staticmethod
    def add_field(model_name, field_name, func):
        RecordFieldExtend(model_name, field_name, func)

    @staticmethod
    def record_value(record, field_name):
        for record_field in RecordFieldExtend._all_record_field:
            if record_field.model_name == record.__class__.__name__ and \
                    record_field.field_name == field_name:
                return record_field.func(record)


class RecordFieldFilter:
    _all_record_field = []

    def __init__(self, model_name, field_name, func):
        self.model_name = model_name
        self.field_name = field_name
        self.func = func
        self._all_record_field.append(self)

    @staticmethod
    def add_filter(model_name, field_names, func):
        RecordFieldFilter(model_name, field_names, func)

    @staticmethod
    def model_class(query):
        return query.column_descriptions[0]['type']

    @staticmethod
    def filter_query(query, field_name, request, request_header):
        for record_field in RecordFieldFilter._all_record_field:
            model_class = RecordFieldFilter.model_class(query)
            if record_field.model_name == model_class.__name__ and \
                    record_field.field_name == field_name:
                return record_field.func(model_class, query, request, request_header)
