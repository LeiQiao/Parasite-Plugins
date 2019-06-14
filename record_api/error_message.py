from base_api_wrapper.http_error import *


def record_field_not_found_error(error_message=''):
    return HTTPSystemError(CustomResponseCode(90102, error_message))


def record_not_found_error(error_message='找不到该记录'):
    return HTTPNotFoundError(CustomResponseCode(90103, error_message))


def fetch_database_error(error_message='数据查询失败'):
    return HTTPSystemError(CustomResponseCode(90104, error_message))


def update_database_error(error_message='数据更新失败'):
    return HTTPSystemError(CustomResponseCode(90105, error_message))
