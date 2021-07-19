from django.shortcuts import render, redirect
from django.http import HttpResponse
from web.forms.account import RegisterModelForm, SendSmsForm, LoginSMSForm, LoginForm
from django.http import JsonResponse
from io import BytesIO
from Tool.local_tool.image_code import check_code
from web import models
from django.db.models import Q
import uuid,datetime


def index(request):
    return HttpResponse('你好')


def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html', {'form': form})
    print(request.POST)

    form = RegisterModelForm(data=request.POST)
    if form.is_valid():
        user_object = form.save()
        price_object = models.PricePolicy.objects.filter(category=1, title="个人免费版").first()
        # print(user_object)
        # print(price_object)
        models.Transaction.objects.create(
            status=2,
            order=uuid.uuid4(),
            user=user_object,
            price_policy=price_object,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now(),
        )
        return JsonResponse({'status': True, 'data': '/login/sms/'})
    return JsonResponse({'status': False, 'error': form.errors})


def send_sms(request):

    #在forms中校验手机号的合法性并生成验证码发送短信存储验证信息到redis
    form = SendSmsForm(request, data=request.GET)
    print('进入验证码生成')
    if form.is_valid():
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})
    # print(type(request.GET.get('phone')))
    # return HttpResponse('成功')


def login_sms(request):
    if request.method == 'GET':
        form = LoginSMSForm()
        return render(request, 'login_sms.html', {'form': form})
    form = LoginSMSForm(request.POST)
    if form.is_valid():
        user_object = form.cleaned_data['phone']
        request.session['user_id'] = user_object.id
        request.session.set_expiry(60 * 60 * 24 * 14)
        return JsonResponse({'status': True, 'data': '/index/'})
    return JsonResponse({'status': False, 'error': form.errors})


def login(request):
    """用户名密码登陆"""
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request, 'login.html', {'form': form})

    form = LoginForm(request, data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user_object = models.UserInfo.objects.filter(Q(email=username) | Q(phone=username)).filter(
            password=password).first()
        if user_object:
            request.session['user_id'] = user_object.id
            request.session.set_expiry(60 * 60 * 24 * 14)
            return redirect('index')
        form.add_error('username', '用户名密码错误')
    return render(request, 'login.html', {'form': form})


def image_code(request):

    image_object, code = check_code()
    request.session['image_code'] = code
    request.session.set_expiry(60)  #主动修改session过期时间为60秒
    stream = BytesIO()
    image_object.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def logout(request):
    request.session.flush()
    return redirect('index')