import pa
import re
import io


class InheritRoute:
    _inherits = {}

    @staticmethod
    def add_route(route, func):
        if route in InheritRoute._inherits:
            InheritRoute._inherits[route].append(func)
        else:
            InheritRoute._inherits[route] = [func]

    @staticmethod
    def inherit_route(route, fp):
        if route in InheritRoute._inherits:
            funcs = InheritRoute._inherits[route]
            for func in funcs:
                fp = func(fp)
                fp.seek(0)
        return fp


def inherit_route(route):
    def decorator(func):
        InheritRoute.add_route(route, func)

    return decorator


def text_replace(fp, pattern, replacement_text, encode='utf8'):
    fp_content = fp.read().decode(encode)
    fp_content = re.sub(pattern, replacement_text, fp_content)
    return io.BytesIO(fp_content.encode(encode))


def text_insert(fp, pattern, text_content, before_pattern=False, encode='utf8'):
    fp_content = fp.read().decode(encode)
    found = re.search(pattern, fp_content)
    if found is None:
        pa.log.warning('SimpleHTMLPlugin: text_insert unable found pattern \'{0}\''.format(pattern))
        return fp

    if before_pattern:
        fp_content = fp_content[:found.span()[0]] + text_content + fp_content[found.span()[0]:]
    else:
        fp_content = fp_content[:found.span()[1]] + text_content + fp_content[found.span()[1]:]
    return io.BytesIO(fp_content.encode(encode))


def text_push(fp, text_content, encode='utf8'):
    return text_insert(fp, '^', text_content, encode=encode)


def text_append(fp, text_content, encode='utf8'):
    return text_insert(fp, '$', text_content, encode=encode)
