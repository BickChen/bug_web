from django import forms
from web import models
from django.core.validators import RegexValidator
from django.core.validators import ValidationError
from bug_web import settings
import random
from Tool.Tencent_tool import sms
from Tool.local_tool import encrypt
from Tool.local_tool.bootstrap import BootStrapForm
from django_redis import get_redis_connection


class RegisterModelForm(BootStrapForm, forms.ModelForm):
    phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    password = forms.CharField(label='密码', widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput())
    code = forms.CharField(label='验证码', widget=forms.TextInput)

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'phone', 'code']

    def clean_username(self):
        print("进入用户名验证")
        username = self.cleaned_data['username']
        exists = models.UserInfo.objects.filter(username=username).exists()
        if exists:
            raise ValidationError('用户名已存在')
        return username

    def clean_email(self):
        print("进入邮箱验证")
        email = self.cleaned_data['email']
        exists = models.UserInfo.objects.filter(email=email).exists()
        if exists:
            raise ValidationError('此邮箱已注册')
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return encrypt.md5(pwd)

    def clean_confirm_password(self):
        print("进入密码验证")
        password = self.cleaned_data['password']
        confirm_password = encrypt.md5(self.cleaned_data['confirm_password'])

        if password != confirm_password:
            raise ValidationError('密码输入不一致')
        return confirm_password

    def clean_phone(self):
        print("进入手机验证")
        phone = self.cleaned_data['phone']
        exists = models.UserInfo.objects.filter(phone=phone).exists()
        if exists:
            raise ValidationError('手机号已注册')
        return phone

    def clean_code(self):
        print("进入验证码验证")
        """
        此处不使用cleande_data.get会出现报错找不到key phone
        因为上面的clean_phone如果验证不通过会直接通过ValidationError抛出错误ValidationError抛出错误后并不会执行return phone
        所以 cleaned_data 中就没有phone的值
        此问题有两种解决方案：
        1、使用cleand_data.get方法
        2、抛出错误时使用self.add_error('phone', '手机号已注册')
        self.add_error只会添加错误，添加错误后会继续执行函数内的代码return phone
        """
        phone = self.cleaned_data.get('phone')
        code = self.cleaned_data['code']

        conn = get_redis_connection()
        redis_code = conn.get(phone)
        if not redis_code:
            raise ValidationError('验证码已失效或未发送成功')
        str_redis_code = redis_code.decode('utf-8')
        if code.strip() != str_redis_code:
            raise ValidationError('验证码错误')
        return str_redis_code


class SendSmsForm(forms.Form):
    print('成功进入')
    phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_phone(self):
        print('进入检测')
        phone = self.cleaned_data['phone']
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE[tpl]
        if not template_id:
            raise ValidationError('短信模版错误')
        print("检测手机号是否存在")
        exists = models.UserInfo.objects.filter(phone=phone).exists()
        if tpl == 'login':
            if not exists:
                raise ValidationError('手机号未注册，请注册后登陆')
        else:
            if exists:
                raise ValidationError('手机号已存在')
        print("生成验证码并存储")
        # 生成验证码发送并存储到redis中
        code = random.randrange(1000, 9999)
        sms_phone = '+86' + phone
        sms.sms(sms_phone, str(code), template_id)
        print("生成验证码成功")
        conn = get_redis_connection()
        conn.set(phone, code, ex=60)

        return phone


class LoginSMSForm(BootStrapForm, forms.Form):
    phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    code = forms.CharField(label='验证码', widget=forms.TextInput)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        user_object = models.UserInfo.objects.filter(phone=phone).first()
        if not user_object:
            raise ValidationError('手机号未注册')
        return user_object

    def clean_code(self):
        code = self.cleaned_data['code']
        phone = self.cleaned_data.get('phone')

        if not phone:
            return code

        conn = get_redis_connection()
        redis_code = conn.get(phone.phone)
        if not redis_code:
            raise ValidationError('验证码已失效或未发送成功')
        str_redis_code = redis_code.decode('utf-8')
        if code.strip() != str_redis_code:
            raise ValidationError('验证码错误')
        return str_redis_code


class LoginForm(BootStrapForm, forms.Form):
    username = forms.CharField(label='邮箱或手机号')
    password = forms.CharField(label='密码', widget=forms.PasswordInput(render_value=True))
    code = forms.CharField(label='验证码', widget=forms.TextInput)

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return encrypt.md5(pwd)

    def clean_code(self):
        code = self.cleaned_data['code']
        session_code = self.request.session.get('image_code')

        if not session_code:
            raise ValidationError('验证码已过期，请重新获取')

        if code != session_code:
            raise ValidationError('验证码输入错误')

        return code
