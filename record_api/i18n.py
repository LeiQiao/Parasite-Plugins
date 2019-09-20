from i18n import *


READ_JSON_BODY_ERROR = I18n.regist(zh_CN='无法解析 json 请求报文，请确认 json 格式是否正确')
PARAMETER_NOT_EXIST_ERROR = I18n.regist(zh_CN='参数 {0} 不存在')
FIELD_NOT_EXIST_ERROR = I18n.regist(zh_CN='未找到字段 \'{0}.{1}\'')
PARAMETER_FORMAT_ERROR = I18n.regist(zh_CN='参数值 \'{0}\' 格式化失败')
PAGINATION_NOT_DIGIT_ERROR = I18n.regist(zh_CN='分页参数必须是数字类型')
PAGINATION_START_ERROR = I18n.regist(zh_CN='起始页码 {0} 必须大于 0')
RESTRICT_DELETE_RECORD_ERROR = I18n.regist(zh_CN='无法删除指定记录，请先删除关联该记录的元素')
