# LDAP 用户相关接口文档

版本号： v1.0.0

修改时间： 2019-05-27

作者： 乔磊


## 获取登陆图形验证码

方法：`GET`

地址：`/user/session`



请求参数：

无



返回参数：

图形验证码的图片内容



Cookies：

接口返回时会设置浏览器 Cookies

| key | 描述 |
|------------|---------------|
| session_id | 登陆或登陆后使用当前 session_id 代表用户登陆 HMAS |



示例：

```python
>>> requests.get('http://127.0.0.1:5002/session')

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



返回参数：

登陆成功后返回状态码 200；失败则返回状态码 401，具体失败请求参考返回内容

|名称|字段类型|描述|
|---|-------|---|
|cn_name|String| 中文名 |
|user_id|String| 域账号用户邮箱 |



示例：

```python
>>> requests.post('http://127.0.0.1:5002/user/login', data={'user_name': 'xxxx@huifu.com', 'password': '*****', 'captcha': '0000'}, cookies={'session_id': 'xxxxxx'}).text

'{
    "data": {
        "cn_name": "xxxx",
        "user_id": "xxxx@huifu.com"
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



返回参数：

返回匹配用户邮箱的用户列表

| 名称    | 字段类型 | 描述           |
| ------- | -------- | -------------- |
| cn_name | String   | 中文名         |
| user_id | String   | 域账号用户邮箱 |



示例：

```python
>>> requests.post('http://127.0.0.1:5002/user/search', data={'user_name': 'san'}, cookies={'session_id': 'xxxxxx'}).text

'{
    "data": [
        {
            "cn_name": "张三",
            "user_id": "san.zhang@huifu.com"
        },
        {
            "cn_name": "王三",
            "user_id": "san.wang@huifu.com"
        },
        {
            "cn_name": "离散",
            "user_id": "san.li@huifu.com"
        }
    ],
    "message": "成功",
    "return_code": "90000"
}'
```

