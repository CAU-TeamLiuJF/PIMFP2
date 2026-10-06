from .error_code import ErrCode


class BizError(Exception):
    def __init__(self, err_code: ErrCode, msg, *args):
        super().__init__(err_code, msg, *args)
        self.code = err_code.code
        self.msg = msg


class BizI18nError(Exception):
    def __init__(self, err_code: ErrCode, *args, **kwargs):
        self.code = err_code.code
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.__class__.__name__}({self.code}, {self.args}, {self.kwargs})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.code}, {self.args}, {self.kwargs})"
