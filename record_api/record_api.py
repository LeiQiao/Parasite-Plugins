from .record_field import *
from .record_event import RecordEventHandler
import pa
from sqlalchemy.orm.attributes import InstrumentedAttribute
from .i18n import *


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

    def get_parameter(self, parameter_name, default_value=None):
        if parameter_name not in self._request:
            return default_value
        return self._request[parameter_name]

    def add_input(self, *args):
        for field in args:
            if isinstance(field, InstrumentedAttribute):
                field = RecordField(field)
            elif not isinstance(field, RecordField):
                raise TypeError('input must be RecordField or RecordFilter: {0}'
                                .format(field.__class__.__name__))

            self._change_field_attribute_to_string(field)
            self._inputs.append(field)

    def add_constrain(self, *args):
        for constrain_filter in args:
            if not isinstance(constrain_filter, RecordFilter):
                raise TypeError('record filter is not type RecordFilter: {0}'
                                .format(constrain_filter.__class__.__name__))
            self._constrains.append(constrain_filter)

    def add_output(self, *args):
        for field in args:
            if isinstance(field, InstrumentedAttribute):
                field = RecordField(field)
            if not isinstance(field, RecordField) or isinstance(field, RecordFilter):
                raise KeyError('output must be RecordField')

            self._change_field_attribute_to_string(field)
            self._outputs.append(field)

    def regist(self):
        if self not in RecordAPI._all_record_api:
            RecordAPI._all_record_api.append(self)

        pa.web_app.add_url_rule(self._route,
                                view_func=RecordAPI._api_handler,
                                methods=[self._method],
                                defaults={'record_api': self})

    def _change_field_attribute_to_string(self, field):
        if not isinstance(field.field_name, InstrumentedAttribute):
            return

        if getattr(self._record_model, field.field_name.key, None) != field.field_name:
            raise KeyError('model \'{0}\' not match the model of field \'{1}\''
                           .format(self._record_model.__name__,
                                   field.field_name))
        field.field_name = field.field_name.key
        if isinstance(field.parameter_name, InstrumentedAttribute):
            field.parameter_name = field.field_name

    @staticmethod
    def _api_handler(record_api):
        return record_api.handle_request()

    def handle_request(self):
        if self._json_data_form:
            try:
                self._request = http_request.json
            except Exception as e:
                pa.log.error(e)
                raise parameter_error(i18n(READ_JSON_BODY_ERROR))
        else:
            if http_request.method == 'POST' or http_request.method == 'PUT' or http_request.method == 'DELETE':
                self._request = http_request.form
            else:
                self._request = http_request.args
        self._request_headers = http_request.headers

        try:
            if self._json_data_form:
                req_str = str(self._request)
            else:
                req_str = str(self._request.to_dict())
            pa.log.info('请求报文: %s', req_str)
        except Exception as e:
            pa.log.error(e)
            pass

        self._event_handler.execute_before_request_handler(self, self._request, self._request_headers)
        self.handle()
        self._response = self._event_handler.execute_after_request_handler(self,
                                                                           self._request,
                                                                           self._response,
                                                                           self._request_headers)

        try:
            pa.log.info('返回报文: %s', str(self._response))
        except Exception as e:
            pa.log.error(e)
            pass

        return custom_success(self._response)

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

    def add_before_request(self, func):
        self._event_handler.add_before_request_handler(func)

    def add_after_request(self, func):
        self._event_handler.add_after_request_handler(func)

    # decorate
    @staticmethod
    def _get_record_api(route, method):
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
            RecordAPI._get_record_api(route, method).add_before_query(func)
        return decorated

    @staticmethod
    def after_query(route, method='GET'):
        def decorated(func):
            RecordAPI._get_record_api(route, method).add_after_query(func)
        return decorated

    @staticmethod
    def before_commit(route, method='GET'):
        def decorated(func):
            RecordAPI._get_record_api(route, method).add_before_commit(func)
        return decorated

    @staticmethod
    def after_commit(route, method='GET'):
        def decorated(func):
            RecordAPI._get_record_api(route, method).add_after_commit(func)
        return decorated

    @staticmethod
    def before_request(route, method='GET'):
        def decorated(func):
            RecordAPI._get_record_api(route, method).add_before_request(func)
        return decorated

    @staticmethod
    def after_request(route, method='GET'):
        def decorated(func):
            RecordAPI._get_record_api(route, method).add_after_request(func)
        return decorated


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
        query = self._record_model.query

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
        if self.page_number is not None and self.page_number.has_value(self._request) and \
                self.page_size is not None and self.page_size.has_value(self._request):
            try:
                page_number = int(self.page_number.request_value(self._request))
                page_size = int(self.page_size.request_value(self._request))
            except Exception as e:
                pa.log.error('RecordAPIPlugin: unable convert page_number or page_size to integer: {0}'.format(e))
                raise parameter_error(i18n(PAGINATION_NOT_DIGIT_ERROR))
            if page_number < 1:
                raise parameter_error(i18n(PAGINATION_START_ERROR))
            query = query.limit(page_size).offset((page_number-1)*page_size)

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
            for field in self._outputs:
                record_json[field.parameter_name] = field.record_value(record)
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
        query = self._record_model.query

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

        records = self._event_handler.execute_after_query_handler(self, [record])
        if len(records) > 0:
            record = records[0]
        else:
            record = None

        if record is None:
            raise record_not_found_error()

        record_json = {}
        for field in self._outputs:
            record_json[field.parameter_name] = field.record_value(record)

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

        self._event_handler.execute_after_commit_handler(self)

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
        query = self._record_model.query

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

        try:
            pa.database.session.commit()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable insert record {0}'.format(e))
            raise update_database_error()

        for record in records:
            RecordFieldEditor.endflush(record)

        self._event_handler.execute_after_commit_handler(self)

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
        query = self._record_model.query

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

        records = self._event_handler.execute_before_delete_handler(self, records)

        if len(records) == 0:
            raise record_not_found_error()

        for record in records:
            try:
                RecordFieldEditor.delete(record)
            except Exception as e:
                raise parameter_error(str(e))

        try:
            for record in records:
                pa.database.session.delete(record)
            pa.database.session.commit()
        except Exception as e:
            pa.log.error('RecordAPIPlugin: unable delete records {0}'.format(e))
            raise update_database_error()

        self._event_handler.execute_after_delete_handler(self)

    # decorate
    @staticmethod
    def route(model, route, method=None, json_data_form=False):
        def decorated(func):
            api = RecordDeleteAPI(model, route, method, json_data_form)
            func(api)
            api.regist()

        return decorated
