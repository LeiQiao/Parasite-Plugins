# LDAP 用户相关接口文档

版本号： v1.0.0

修改时间： 2019-06-27

作者： 乔磊



## 获取 TOKEN

方法：`GET`

地址：`/user/token`



请求参数：

无



返回参数：

| 名称  | 字段类型 | 描述  |
| ----- | -------- | ----- |
| token | String   | token |



示例：

```python
>>> requests.get('http://127.0.0.1:5002/user/token').text

'{
    "data": {
        "token": "xxxx"
    },
    "message": "登录成功",
    "return_code": "90000"
}'
```



## 获取登陆图形验证码

方法：`GET`

地址：`/user/captcha`



请求参数：

| 名称  | 字段类型 | 必须 | 描述                           |
| ----- | -------- | ---- | ------------------------------ |
| token | String   | Y    | 获取 token 接口返回的 token 值 |



返回参数：

图形验证码的图片内容



示例：

```python
>>> requests.get('http://127.0.0.1:5002/captcha?token=xxxx')

<Response [200]>
```





## 登陆

方法：`POST`

地址：`/user/login`



请求参数：

|名称|字段类型|必须|描述|
|---|-------|---|----|
|user_name|String| Y | 域账号用户邮箱 |
|password| String| Y | 域账号密码 |
|captcha | String | Y | 图形验证码 |
|token | String | Y | token |



返回参数：

登陆成功后返回状态码 200；失败则返回状态码 401，具体失败请求参考返回内容

|名称|字段类型|描述|
|---|-------|---|
|cn_name|String| 中文名 |
|user_id|String| 域账号用户邮箱 |

* 登录成功后所有需要用户鉴权的接口都需要将 token 添加到请求体中

示例：

```python
>>> requests.post('http://127.0.0.1:5002/user/login', data={'user_name': 'xxxx@yyyyy.com', 'password': '*****', 'captcha': '0000', 'token': 'xxxx'}).text

'{
    "data": {
        "cn_name": "xxxx",
        "user_id": "xxxx@yyyyy.com"
    },
    "message": "登录成功",
    "return_code": "90000"
}'
```



## 查询用户

方法：`GET`

地址：`/user/search`



请求参数：

| 名称      | 字段类型 | 必须 | 描述           |
| --------- | -------- | ---- | -------------- |
| user_name | String   | Y    | 域账号用户邮箱 |
| token     | String   | Y    | token          |



返回参数：

返回匹配用户邮箱的用户列表

| 名称    | 字段类型 | 描述           |
| ------- | -------- | -------------- |
| cn_name | String   | 中文名         |
| user_id | String   | 域账号用户邮箱 |



示例：

```python
>>> requests.post('http://127.0.0.1:5002/user/search', data={'user_name': 'san', 'token': 'xxxxxx'}).text

'{
    "data": [
        {
            "cn_name": "张三",
            "user_id": "san.zhang@yyyyy.com"
        },
        {
            "cn_name": "王三",
            "user_id": "san.wang@yyyyy.com"
        },
        {
            "cn_name": "离散",
            "user_id": "san.li@yyyyy.com"
        }
    ],
    "message": "成功",
    "return_code": "90000"
}'
```

