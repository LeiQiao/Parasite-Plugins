class RecordEventHandler:
    _global_before_query_handlers = []
    _global_after_query_handlers = []
    _global_before_commit_handlers = []
    _global_after_commit_handlers = []
    _global_before_delete_handlers = []
    _global_after_delete_handlers = []
    _global_before_request_handlers = []
    _global_after_request_handlers = []
    _global_request_error_handlers = []

    def __init__(self):
        self._before_query_handlers = []
        self._after_query_handlers = []
        self._before_commit_handlers = []
        self._after_commit_handlers = []
        self._before_delete_handlers = []
        self._after_delete_handlers = []
        self._before_request_handlers = []
        self._after_request_handlers = []
        self._request_error_handlers = []

    # add global handler
    @staticmethod
    def add_global_before_query_handler(handler):
        RecordEventHandler._global_before_query_handlers.append(handler)

    @staticmethod
    def add_global_after_query_handler(handler):
        RecordEventHandler._global_after_query_handlers.append(handler)

    @staticmethod
    def add_global_before_commit_handler(handler):
        RecordEventHandler._global_before_commit_handlers.append(handler)

    @staticmethod
    def add_global_after_commit_handler(handler):
        RecordEventHandler._global_after_commit_handlers.append(handler)

    @staticmethod
    def add_global_before_delete_handler(handler):
        RecordEventHandler.add_global_before_delete_handler(handler)

    @staticmethod
    def add_global_after_delete_handler(handler):
        RecordEventHandler.add_global_after_delete_handler(handler)

    @staticmethod
    def add_global_before_request_handler(handler):
        RecordEventHandler._global_before_request_handlers.append(handler)

    @staticmethod
    def add_global_after_request_handler(handler):
        RecordEventHandler._global_after_request_handlers.append(handler)

    @staticmethod
    def add_global_request_error_handler(handler):
        RecordEventHandler._global_request_error_handlers.append(handler)

    # add op handler
    def add_before_query_handler(self, handler):
        self._before_query_handlers.append(handler)

    def add_after_query_handler(self, handler):
        self._after_query_handlers.append(handler)

    def add_before_commit_handler(self, handler):
        self._before_commit_handlers.append(handler)

    def add_after_commit_handler(self, handler):
        self._after_commit_handlers.append(handler)

    def add_before_delete_handler(self, handler):
        self._before_delete_handlers.append(handler)

    def add_after_delete_handler(self, handler):
        self._after_delete_handlers.append(handler)

    def add_before_request_handler(self, handler):
        self._before_request_handlers.append(handler)

    def add_after_request_handler(self, handler):
        self._after_request_handlers.append(handler)

    def add_request_error_handler(self, handler):
        self._request_error_handlers.append(handler)

    # execute op handler
    def execute_before_query_handler(self, record_api, query):
        for handler in RecordEventHandler._global_before_query_handlers + self._before_query_handlers:
            query = handler(record_api, query)
        return query

    def execute_after_query_handler(self, record_api, records):
        for handler in RecordEventHandler._global_after_query_handlers + self._after_query_handlers:
            records = handler(record_api, records)
        return records

    def execute_before_commit_handler(self, record_api, records, new_record):
        for handler in RecordEventHandler._global_before_commit_handlers + self._before_commit_handlers:
            records = handler(record_api, records, new_record)
        return records

    def execute_after_commit_handler(self, record_api, records):
        for handler in RecordEventHandler._global_after_commit_handlers + self._after_commit_handlers:
            handler(record_api, records)

    def execute_before_delete_handler(self, record_api, records):
        for handler in RecordEventHandler._global_before_delete_handlers + self._before_delete_handlers:
            records = handler(record_api, records)
        return records

    def execute_after_delete_handler(self, record_api):
        for handler in RecordEventHandler._global_after_delete_handlers + self._after_delete_handlers:
            handler(record_api)

    def execute_before_request_handler(self, record_api, request, request_headers):
        for handler in RecordEventHandler._global_before_request_handlers + self._before_request_handlers:
            handler(record_api, request, request_headers)

    def execute_after_request_handler(self, record_api, request, response, request_headers):
        for handler in RecordEventHandler._global_after_request_handlers + self._after_request_handlers:
            response = handler(record_api, request, response, request_headers)
        return response

    def execute_request_error_handler(self, record_api, request, error, request_headers):
        for handler in RecordEventHandler._global_request_error_handlers + self._request_error_handlers:
            error = handler(record_api, request, error, request_headers)
        return error

    # decorate
    @staticmethod
    def before_query(func):
        RecordEventHandler.add_global_before_query_handler(func)

    @staticmethod
    def after_query(func):
        RecordEventHandler.add_global_after_query_handler(func)

    @staticmethod
    def before_commit(func):
        RecordEventHandler.add_global_before_commit_handler(func)

    @staticmethod
    def after_commit(func):
        RecordEventHandler.add_global_after_commit_handler(func)

    @staticmethod
    def before_delete(func):
        RecordEventHandler.add_global_before_delete_handler(func)

    @staticmethod
    def after_delete(func):
        RecordEventHandler.add_global_after_delete_handler(func)

    @staticmethod
    def before_request(func):
        RecordEventHandler.add_global_before_request_handler(func)

    @staticmethod
    def after_request(func):
        RecordEventHandler.add_global_after_request_handler(func)

    @staticmethod
    def request_error(func):
        RecordEventHandler.add_global_request_error_handler(func)


# prevent pep8 not used warning
def unused(*unused_args, **unused_kwargs):
    return unused_args, unused_kwargs
