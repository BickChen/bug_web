# -*- coding: utf-8 -*-
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.sms.v20190711 import sms_client, models
from bug_web.settings import SMS_CONF,TENCENT_SMS_TEMPLATE
import random


def sms(phone, code, tpl):

    try:
        #print(SMS_CONF['secretID'], SMS_CONF['secretKey'])
        cred = credential.Credential(SMS_CONF['secretID'], SMS_CONF['secretKey'])
        client = sms_client.SmsClient(cred, SMS_CONF['regio'])
        req = models.SendSmsRequest()
        # 短信应用 ID: 在 [短信控制台] 添加应用后生成的实际 SDKAppID，例如1400006666
        req.SmsSdkAppid = SMS_CONF['SmsSdkAppid']
        # 短信签名内容: 使用 UTF-8 编码，必须填写已审核通过的签名，可登录 [短信控制台] 查看签名信息
        req.Sign = SMS_CONF['Sign']
        # 下发手机号码，采用 e.164 标准，+[国家或地区码][手机号]
        # 例如+8613711112222， 其中前面有一个+号 ，86为国家码，13711112222为手机号，最多不要超过200个手机号
        req.PhoneNumberSet = [phone,]
        # 模板 ID: 必须填写已审核通过的模板 ID，可登录 [短信控制台] 查看模板 ID
        req.TemplateID = tpl
        # 模板参数: 若无模板参数，则设置为空
        req.TemplateParamSet = [str(code), SMS_CONF['time_out']]
        # 通过 client 对象调用 SendSms 方法发起请求。注意请求方法名与请求对象是对应的
        resp = client.SendSms(req)
        # 输出 JSON 格式的字符串回包

        return resp.to_json_string(indent=2)

    except TencentCloudSDKException as err:
        return err


if __name__ in "__main__":
    phone = '+8615188426858'
    code = random.randrange(1000, 9999)
    n = sms(phone, code, TENCENT_SMS_TEMPLATE['register'])
    print(n)