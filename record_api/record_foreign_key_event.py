from .record_api import *


def restrtct_delete(condition):
    if hasattr(condition.left, '_annotations'):
        model_class = getattr(condition.left, '_annotations')['parententity'].class_
    elif hasattr(condition.right, '_annotations'):
        model_class = getattr(condition.right, '_annotations')['parententity'].class_
    else:
        raise ModuleNotFoundError()

    return model_class.query.filter(condition).count() == 0


def cascade_delete(condition):
    if hasattr(condition.left, '_annotations'):
        model_class = getattr(condition.left, '_annotations')['parententity'].class_
        field_name = condition.left.key
    elif hasattr(condition.right, '_annotations'):
        model_class = getattr(condition.right, '_annotations')['parententity'].class_
        field_name = condition.right.key
    else:
        raise ModuleNotFoundError()

    if hasattr(condition.left, 'value'):
        value = condition.left.value
    elif hasattr(condition.right, 'value'):
        value = condition.right.value
    else:
        raise ModuleNotFoundError()

    delete_api = RecordDeleteAPI(model_class, None)
    delete_api.add_input(RecordFilter(getattr(model_class, field_name)))
    try:
        delete_api.handle_request({field_name: value}, {})
    except HTTPNotFoundError as e:
        str(e)
        return
    except Exception as e:
        raise e
