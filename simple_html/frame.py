import re
import io


class FrameDecorator:
    _decorators = {}

    @staticmethod
    def get_frame(name):
        if name in FrameDecorator._decorators:
            return FrameDecorator._decorators[name]
        return None

    @staticmethod
    def set_frame(name, frame):
        FrameDecorator._decorators[name] = frame

    @staticmethod
    def remove_frame(name):
        if name not in FrameDecorator._decorators:
            return
        del FrameDecorator._decorators[name]

    @staticmethod
    def decorator_route(route, fp):
        for name, frame in FrameDecorator._decorators.items():
            if frame.is_inherit_route(route):
                fp = frame.render(route, fp)
                fp.seek(0)
                return fp
        return fp


class BaseFrame:
    START_TAG = '{%'
    END_TAG = '%}'

    def add_routes(self, *args):
        inherit_routes = getattr(self, 'inherit_routes', None)
        if inherit_routes is None:
            inherit_routes = []
            setattr(self, 'inherit_routes', inherit_routes)
        for r in args:
            if r not in inherit_routes:
                inherit_routes.append(r)

    def remove_routes(self, *args):
        inherit_routes = getattr(self, 'inherit_routes', None)
        if inherit_routes is None:
            return

        for r in args:
            if r in inherit_routes:
                inherit_routes.remove(r)

    def is_inherit_route(self, route):
        inherit_routes = getattr(self, 'inherit_routes', None)
        if inherit_routes is None:
            return False

        return route in inherit_routes

    def render(self, route, route_fp, encode='utf8'):
        raise NotImplementedError('class \'{0}\' has not implemented function \'render\''
                                  .format(self.__class__.__name__))

    @staticmethod
    def _render(frame_content, route_content, keyword, start_tag='\{\%', end_tag='\%\}'):
        pattern = '{0}[\s]*{1}[\s]*{2}'.format(start_tag, keyword, end_tag)
        render_content = re.sub(pattern, route_content, frame_content)
        return render_content


class SimpleFrame(BaseFrame):
    def __init__(self, title=''):
        self.title = title
        self.keywords = {}

    def add_keyword(self, keyword, r):
        self.keywords[keyword] = r

    def render(self, route, route_fp, encode='utf8'):
        render_content = route_fp.read().decode(encode)
        for k, r in self.keywords.items():
            r = self._to_js_code(r)
            render_content = BaseFrame._render(render_content, r, k)
        fp = io.BytesIO(render_content.encode(encode))
        return fp

    def _to_js_code(self, r):
        if isinstance(r, str) or isinstance(r, int) or isinstance(r, float):
            return r
        elif isinstance(r, list):
            s = '['
            for v in r:
                if isinstance(v, str):
                    v = '\"{0}\"'.format(v)
                else:
                    v = self._to_js_code(v)
                s += '{0}, '.format(v)
            s = s[:-2] + ']'
            return s
        elif isinstance(r, dict):
            s = '{'
            for k, v in r.items():
                if isinstance(v, str):
                    v = '\"{0}\"'.format(v)
                else:
                    v = self._to_js_code(v)
                s += '{0}: {1}, '.format(k, v)
            s = s[:-2] + '}'
            return s
