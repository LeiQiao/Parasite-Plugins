from .record_field import *
from .record_event import RecordEventHandler
import pa
from sqlalchemy.orm.attributes import InstrumentedAttribute
from .i18n import *
from sqlalchemy import exc
from .model_decorator import ExtraColumn


class RecordAPI:
    _all_record_api = []

    def __init__(self, model, route, method=None, json_data_form=False):
        self._record_model = model
        self._route = route
        self._method = method
        self._inputs = []
        self._outputs = []
        self._constrains = []
        self._request = None
        self._request_headers = {}
        self._response = None
        self._json_data_form = json_data_form

        self._event_handler = RecordEventHandler()

    def get_route(self):
        return self._route

    def get_method(self):
        return self._method

    def get_model(self):
        return self._record_model

    def get_parameter(self, parameter_name, default_value=None, accept_empty=True):
        if parameter_name not in self._request:
            return default_value
        value = self._request[parameter_name]
        if isinstance(value, int):
            return value
        if value is None:
            return default_value
        if not accept_empty and value == '':
            return default_value
        return value

    @staticmethod
    def get_request_file(file_name):
        if file_name is None:
            return http_request.files

        if file_name in http_request.files:
            return http_request.files[file_name]
        else:
            return None

    def add_input(self, *args):
        for field in args:
            if isinstance(field, InstrumentedAttribute):
                field = RecordField(field)
            elif not isinstance(field, RecordField):
                raise TypeError('input must be RecordField or RecordFilter: {0}'
                                .format(field.__class__.__name__))

            self._change_field_attribute_to_string(field)
            self._inputs.append(field)

    def inputs(self):
        return self._inputs

    def add_constrain(self, *args):
        for constrain_filter in args:
            if not isinstance(constrain_filter, RecordFilter):
                raise TypeError('record filter is not type RecordFilter: {0}'
                                .format(constrain_filter.__class__.__name__))
            self._constrains.append(constrain_filter)

    def constrains(self):
        return self._constrains

    def add_output(self, *args):
        for field in args:
            if isinstance(field, InstrumentedAttribute):
                field = RecordField(field)
            if isinstance(field, ExtraColumn):
                field = RecordField(field)
            if not isinstance(field, RecordField) or isinstance(field, RecordFilter):
                raise KeyError('output must be RecordField')

            self._change_field_attribute_to_string(field)
            self._outputs.append(field)

    def outputs(self):
        return self._outputs

    def regist(self):
        if self not in RecordAPI._all_record_api:
            RecordAPI._all_record_api.append(self)

        pa.web_app.add_url_rule(self._route,
                                view_func=RecordAPI._api_handler,
                                methods=[self._method],
                                defaults={'record_api': self})

    def _change_field_attribute_to_string(self, field):
        if isinstance(field.field_name, InstrumentedAttribute):
            if getattr(self._record_model, field.field_name.key, None) != field.field_name:
                raise KeyError('model \'{0}\' not match the model of field \'{1}\''
                               .format(self._record_model.__name__,
                                       field.field_name))
            field.field_name = field.field_name.key
            if isinstance(field.parameter_name, InstrumentedAttribute):
                field.parameter_name = field.field_name
        elif isinstance(field.field_name, ExtraColumn):
            if field.default is None:
                field.default = field.field_name.default
            field_name = None
            for attr in dir(self._record_model):
                attr_value = getattr(self._record_model, attr)
                if isinstance(attr_value, ExtraColumn) and attr_value == field.field_name:
                    field_name = attr
                    break
            field.field_name = field_name
            if isinstance(field.parameter_name, ExtraColumn):
                field.parameter_name = field.field_name

    @staticmethod
    def _api_handler(record_api):
        return record_api.handle_http_request()

    def handle_http_request(self):
        pa.log.info('请求: %s', self._route)

        if self._json_data_form:
            try:
                request = http_request.json
            except Exception as e:
                pa.log.error(e)
                raise parameter_error(i18n(READ_JSON_BODY_ERROR))
        else:
            if http_request.method == 'POST' or http_request.method == 'PUT' or http_request.method == 'DELETE':
                request = http_request.form
            else:
                request = http_request.args
        request_headers = http_request.headers

        try:
            if self._json_data_form:
                req_str = str(request)
            else:
                req_str = str(request.to_dict())
            pa.log.info('请求报文: %s', req_str)
        except Exception as e:
            pa.log.error(e)
            pass

        response = self.handle_request(request, request_headers)

        try:
            pa.log.info('返回报文: %s', str(response))
        except Exception as e:
            pa.log.error(e)
            pass

        return custom_success(response)

    def handle_request(self, request, request_headers):
        self._request = request
        self._request_headers = request_headers

        self._event_handler.execute_before_request_handler(self, self._request, self._request_headers)
        try:
            self.handle()
        except Exception as e:
            raise self._event_handler.execute_request_error_handler(self, self._request, e, self._request_headers)
        self._response = self._event_handler.execute_after_request_handler(self,
                                                                           self._request,
                                                                           self._response,
                                                                           self._request_headers)

        return self._response

    # Overridable -- handle model event
    def handle(self):
        pass

    def add_before_query(self, func):
        self._event_handler.add_before_query_handler(func)

    def add_after_query(self, func):
        self._event_handler.add_after_query_handler(func)

    def add_before_commit(self, func):
        self._event_handler.add_before_commit_handler(func)

    def add_after_commit(self, func):
        self._event_handler.add_after_commit_handler(func)

    def add_before_delete(self, func):
        self._event_handler.add_before_delete_handler(func)

    def add_after_delete(self, func):
        self._event_handler.add_after_delete_handler(func)

    def add_before_request(self, func):
        self._event_handler.add_before_request_handler(func)

    def add_after_request(self, func):
        self._event_handler.add_after_request_handler(func)

    def add_request_error(self, func):
        self._event_handler.add_request_error_handler(func)

    # decorate
    @staticmethod
    def get_record_api(route, method):
        for api in RecordAPI._all_record_api:
            if api.get_route() != route:
                continue
            if api.get_method().upper() != method.upper():
                continue
            return api
        raise ModuleNotFoundError('unable found route \'{0} {1}\''.format(method.upper(), route))

    @staticmethod
    def before_query(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_before_query(func)
        return decorated

    @staticmethod
    def after_query(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_after_query(func)
        return decorated

    @staticmethod
    def before_commit(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_before_commit(func)
        return decorated

    @staticmethod
    def after_commit(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_after_commit(func)
        return decorated

    @staticmethod
    def before_delete(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_before_delete(func)
        return decorated

    @staticmethod
    def after_delete(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_after_delete(func)
        return decorated

    @staticmethod
    def before_request(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_before_request(func)
        return decorated

    @staticmethod
    def after_request(route, method='GET'):
        def decorated(func):
            RecordAPI.get_record_api(route, method).add_after_request(func)
        return decorated

    # tools
    def make_query(self):
        return self._record_model.query

    def trim_join_results(self, records):
        rcds = []
        for record in records:
            rcds.append(self.get_model_record(record))
        return rcds

    def get_model_record(self, record):
        if isinstance(record, tuple):
            model_record = None
            for rcd in record:
                if rcd.__class__ == self._record_model:
                    model_record = rcd
                    break
            if model_record is None:
                if isinstance(self._record_model, pa.database.Model):
                    return None
                model_record = self._record_model()
            # set ExtraColumn(ri.Column) values
            model_class = model_record.__class__
            for attr in dir(model_class):
                attr_value = getattr(model_class, attr)
                if not isinstance(attr_value, ExtraColumn):
                    continue
                # ignored if object's ExtraColumn is already set by outside
                obj_attr_value = getattr(model_record, attr)
                if not isinstance(obj_attr_value, ExtraColumn):
                    continue
                record_attr = attr
                record_default = attr_value.default
                if attr_value.field_name is not None:
                    record_attr = attr_value.field_name
                if hasattr(record, record_attr):
                    value = getattr(record, record_attr)
                    setattr(model_record, attr, value)
                else:
                    if callable(record_default):
                        record_default = record_default()
                    setattr(model_record, attr, record_default)
            return model_record
        return record


class RecordListAPI(RecordAPI):
    def __init__(self, model, route, method=None, json_data_form=False):
        if method is None:
            method = 'GET'
        super(RecordListAPI, self).__init__(model, route, method, json_data_form)
        self.page_number = None
        self.page_size = None
        self.total_count = None

    def add_pagination(self,
                       page_number=RecordFilter('page_number', required=False),
                       page_size=RecordFilter('page_size', required=False),
                       total_count=RecordField('total_count')):
        self.page_number = page_number
        self.page_size = page_size
        self.total_count = total_count

    def handle(self):
        query = self.make_query()

        for record_filter in self._inputs:
            if not isinstance(record_filter, RecordFilter):
                pa.log.warning('RecordAPIPlugin: list record method unable query non filter: {0}:{1}'
                               .format(record_filter.field_name, record_filter.parameter_name))
                continue
            query = record_filter.filter_query(self._request, query, self._request_headers)

        for constrain_filter in self._constrains:
            query = constrain_filter.filter_query(self._request, query, self._request_headers)

        query = self._event_handler.execute_before_query_handler(self, query)

        record_count_query = query
        if self.page_size is not None and self.page_size.has_value(self._request):
            try:
                page_size = int(self.page_size.request_value(self._request))
            except Exception as e:
                pa.log.error('RecordAPIPlugin: unable convert page_size to integer: {0}'.format(e))
                raise parameter_error(i18n(PAGINATION_NOT_DIGIT_ERROR))
            query = query.limit(page_size)

            if self.page_number is not None and self.page_number.has_value(self._request):
                try:
                    page_number = int(self.page_number.request_value(self._request))
                except Exception as e:
                    pa.log.error('RecordAPIPlugin: unable convert page_number to integer: {0}'.format(e))
                    raise parameter_error(i18n(PAGINATION_NOT_DIGIT_ERROR))
                if page_number < 1:
                    raise parameter_error(i18n(PAGINATION_START_ERROR).format(self.page_number.parameter_name))
                query = query.offset((page_number-1)*page_size)

        try:
            all_records = query.all()
            total_count = record_count_query.count()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable fetch all records {0}'.format(e))
            raise fetch_database_error()

        all_records = self._event_handler.execute_after_query_handler(self, all_records)

        records_json = []
        for record in all_records:
            record_json = {}
            model_record = self.get_model_record(record)
            for field in self._outputs:
                if isinstance(field, JoinedRecordField):
                    record_json[field.parameter_name] = field.record_value(record)
                else:
                    record_json[field.parameter_name] = field.record_value(model_record)
            records_json.append(record_json)

        self._response = {
            'data_list': records_json
        }

        if self.total_count is not None:
            self._response[self.total_count.parameter_name] = total_count

    # decorate
    @staticmethod
    def route(model, route, method=None, json_data_form=False):
        def decorated(func):
            api = RecordListAPI(model, route, method, json_data_form)
            func(api)
            api.regist()

        return decorated


class RecordGetAPI(RecordAPI):
    def __init__(self, model, route, method=None, json_data_form=False):
        if method is None:
            method = 'GET'
        super(RecordGetAPI, self).__init__(model, route, method, json_data_form)

    def handle(self):
        query = self.make_query()

        for record_filter in self._inputs:
            if not isinstance(record_filter, RecordFilter):
                pa.log.warning('RecordAPIPlugin: get record method unable query non filter: {0}:{1}'
                               .format(record_filter.field_name, record_filter.parameter_name))
                continue
            query = record_filter.filter_query(self._request, query, self._request_headers)

        for constrain_filter in self._constrains:
            query = constrain_filter.filter_query(self._request, query, self._request_headers)

        query = self._event_handler.execute_before_query_handler(self, query)

        try:
            record = query.first()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable fetch record {0}'.format(e))
            raise fetch_database_error()

        records = []
        if record is not None:
            records.append(record)

        records = self._event_handler.execute_after_query_handler(self, records)

        if len(records) > 0:
            record = records[0]
        else:
            record = None

        if record is None:
            raise record_not_found_error()

        model_record = self.get_model_record(record)

        record_json = {}
        for field in self._outputs:
            if isinstance(field, JoinedRecordField):
                record_json[field.parameter_name] = field.record_value(record)
            else:
                record_json[field.parameter_name] = field.record_value(model_record)


        self._response = record_json

    # decorate
    @staticmethod
    def route(model, route, method=None, json_data_form=False):
        def decorated(func):
            api = RecordGetAPI(model, route, method, json_data_form)
            func(api)
            api.regist()

        return decorated


class RecordAddAPI(RecordAPI):
    def __init__(self, model, route, method=None, json_data_form=False):
        if method is None:
            method = 'POST'
        super(RecordAddAPI, self).__init__(model, route, method, json_data_form)

    def handle(self):
        new_record = self._record_model()

        for record_field in self._inputs:
            if not isinstance(record_field, RecordField):
                pa.log.warning('RecordAPIPlugin: add record method unable process non field: {0}:{1}'
                               .format(record_field.field_name, record_field.parameter_name))
                continue
            record_field.set_value(self._request, new_record)
        try:
            RecordFieldEditor.flush(new_record)
        except Exception as e:
            raise parameter_error(str(e))

        for constrain_filter in self._constrains:
            constrain_filter.filter_query(self._request, None, self._request_headers)

        new_records = self._event_handler.execute_before_commit_handler(self, [new_record], new_record=True)
        new_record = new_records[0]

        try:
            pa.database.session.add(new_record)
            pa.database.session.commit()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable insert record {0}'.format(e))
            raise update_database_error()

        RecordFieldEditor.endflush(new_record)
        RecordFieldEditor.endadd(new_record)

        self._event_handler.execute_after_commit_handler(self, [new_record])

        record_json = {}
        for field in self._outputs:
            record_json[field.parameter_name] = field.record_value(new_record)

        self._response = record_json

    # decorate
    @staticmethod
    def route(model, route, method=None, json_data_form=False):
        def decorated(func):
            api = RecordAddAPI(model, route, method, json_data_form)
            func(api)
            api.regist()

        return decorated


class RecordEditAPI(RecordAPI):
    def __init__(self, model, route, method=None, json_data_form=False):
        if method is None:
            method = 'PUT'
        super(RecordEditAPI, self).__init__(model, route, method, json_data_form)

    def handle(self):
        query = self.make_query()

        for record_field in self._inputs:
            if not isinstance(record_field, RecordFilter):
                continue
            query = record_field.filter_query(self._request, query, self._request_headers)

        for constrain_filter in self._constrains:
            query = constrain_filter.filter_query(self._request, query, self._request_headers)

        query = self._event_handler.execute_before_query_handler(self, query)

        try:
            records = query.all()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable fetch records {0}'.format(e))
            raise fetch_database_error()

        records = self._event_handler.execute_after_query_handler(self, records)

        records = self.trim_join_results(records)

        for record in records:
            for record_field in self._inputs:
                if isinstance(record_field, RecordFilter):
                    continue
                record_field.set_value(self._request, record)
            try:
                RecordFieldEditor.flush(record)
            except Exception as e:
                raise parameter_error(str(e))

        records = self._event_handler.execute_before_commit_handler(self, records, new_record=False)

        if len(records) == 0:
            raise record_not_found_error()

        try:
            pa.database.session.commit()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable insert record {0}'.format(e))
            raise update_database_error()

        for record in records:
            RecordFieldEditor.endflush(record)

        self._event_handler.execute_after_commit_handler(self, records)

        records_json = []
        for record in records:
            record_json = {}
            for field in self._outputs:
                record_json[field.parameter_name] = field.record_value(record)
            records_json.append(record_json)

        if len(records_json) == 1:
            self._response = records_json[0]
        else:
            self._response = records_json

    # decorate
    @staticmethod
    def route(model, route, method=None, json_data_form=False):
        def decorated(func):
            api = RecordEditAPI(model, route, method, json_data_form)
            func(api)
            api.regist()

        return decorated


class RecordDeleteAPI(RecordAPI):
    def __init__(self, model, route, method=None, json_data_form=False):
        if method is None:
            method = 'DELETE'
        super(RecordDeleteAPI, self).__init__(model, route, method, json_data_form)

    def regist(self):
        if len(self._inputs) == 0:
            raise PermissionError('unable remove all record of \'{0}\''.format(self._record_model.__name__))
        for record_field in self._inputs:
            if not isinstance(record_field, RecordFilter):
                raise TypeError('remove record method unable process field: {0},'
                                ' because it is not RecordFilter'
                                .format(record_field.field_name))

        super(RecordDeleteAPI, self).regist()

    def handle(self):
        query = self.make_query()

        for record_field in self._inputs:
            query = record_field.filter_query(self._request, query, self._request_headers)

        for constrain_filter in self._constrains:
            query = constrain_filter.filter_query(self._request, query, self._request_headers)

        query = self._event_handler.execute_before_query_handler(self, query)

        try:
            records = query.all()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable fetch records {0}'.format(e))
            raise fetch_database_error()

        records = self._event_handler.execute_after_query_handler(self, records)

        records = self.trim_join_results(records)

        records = self._event_handler.execute_before_delete_handler(self, records)

        if len(records) == 0:
            raise record_not_found_error()

        for i in range(len(records)):
            if isinstance(records[i], tuple):
                for rcd in records[i]:
                    if rcd.__class__ == self._record_model:
                        records[i] = rcd
                        break

        for record in records:
            try:
                RecordFieldEditor.delete(record)
            except Exception as e:
                raise parameter_error(str(e))

        try:
            for record in records:
                pa.database.session.delete(record)
            pa.database.session.commit()
        except exc.IntegrityError as e:
            pa.log.error('RecordAPIPlugin: unable delete records {0}'.format(e))
            raise parameter_error(i18n(RESTRICT_DELETE_RECORD_ERROR))
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable delete records {0}'.format(e))
            raise update_database_error()

        for record in records:
            try:
                RecordFieldEditor.enddelete(record)
            except Exception as e:
                raise parameter_error(str(e))

        self._event_handler.execute_after_delete_handler(self)

    # decorate
    @staticmethod
    def route(model, route, method=None, json_data_form=False):
        def decorated(func):
            api = RecordDeleteAPI(model, route, method, json_data_form)
            func(api)
            api.regist()

        return decorated
