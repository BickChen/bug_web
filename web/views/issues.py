from django.shortcuts import render, reverse, HttpResponseRedirect
from web.forms.issues import IssuesModelForm, IssuesReplyModelForm, ProjectInviteModelForm
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from Tool.local_tool.pagination import Pagination
from web import models
from web.models import ProjectUser
from Tool.local_tool.encrypt import uid
import json


class CheckFilter(object):
    def __init__(self, name, data_list, request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            ck = ""
            value_list = self.request.GET.getlist(self.name)
            # print(value_list, key)
            if key in value_list:
                ck = "checked"
                value_list.remove(key)  # 改变value_list中的值并不会影响下一次循环所GET.getlist的值
            else:
                value_list.append(key)

            """
            ['danger'] danger
            [] danger
            /manage/13/issues/?
            ______________________________________________________
            ['danger'] warning
            ['danger', 'warning'] warning
            /manage/13/issues/?priority=danger&priority=warning
            ______________________________________________________
            ['danger'] success
            ['danger', 'success'] success
            /manage/13/issues/?priority=danger&priority=success
            ______________________________________________________
            [] 1
            ['1'] 1
            /manage/13/issues/?priority=danger&status=1
            ______________________________________________________
            [] 2
            ['2'] 2
            /manage/13/issues/?priority=danger&status=2
            ______________________________________________________
            """
            # print(value_list, key)
            # 为自己生成URL
            query_dict = self.request.GET.copy()      #拷贝当前URL后面的参数
            # print(query_dict)
            query_dict._mutable = True                #允许修改query_dict对象
            query_dict.setlist(self.name, value_list) #修改字典中self.filter的值

            #是否有分页参数存在判断
            """
            当筛选和分页结合使用的时候
            因为筛选后不需要分页的参数所以要把分页的参数给删除掉
            默认为第一页
            """
            if "page" in query_dict:
                query_dict.pop("page")

            #删除点击取消所有筛选添加后url后面因query_dict.urlencode()生成的？号
            param_url = query_dict.urlencode()
            if param_url:
                url = "{}?{}".format(self.request.path_info, param_url)
            else:
                url = self.request.path_info
            # print(url)
            # print("______________________________________________________")
            html = '<a class="cell" href="{url}"><input type="checkbox" {ck} /><label>{text}</label></a>'.format(
                url=url, ck=ck, text=text)
            yield mark_safe(html)


class SelectFilter(object):
    def __init__(self, name, data_list, request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        yield mark_safe("<select class='select2' multiple='multiple' style='width:100%;' >")
        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            selected = ""
            value_list = self.request.GET.getlist(self.name)
            if key in value_list:
                selected = "selected"
                value_list.remove(key)  # 改变value_list中的值并不会影响下一次循环所GET.getlist的值
            else:
                value_list.append(key)

            query_dict = self.request.GET.copy()      #拷贝当前URL后面的参数
            # print(query_dict)
            query_dict._mutable = True                #允许修改query_dict对象
            query_dict.setlist(self.name, value_list) #修改字典中self.filter的值

            if "page" in query_dict:
                query_dict.pop("page")

            # 删除点击取消所有筛选添加后url后面因query_dict.urlencode()生成的？号
            param_url = query_dict.urlencode()
            if param_url:
                url = "{}?{}".format(self.request.path_info, param_url)
            else:
                url = self.request.path_info
            html = "<option value='{url}' {selected}>{text}</option>".format(url=url, selected=selected, text=text)
            yield mark_safe(html)
        yield mark_safe("</select>")


def issues(request, project_id):
    """展示任务列表&创建任务&问题筛选功能"""
    if request.method == 'GET':
        form = IssuesModelForm(request)
        # 设置允许筛选查询的类型
        allow_filter_name = ['issues_type', 'status', 'priority', 'assign', 'attention']
        # 筛选数据（根据用户通过GET传过来的参数实现）
        # ?status=1&status=2&issues_type=1
        condition = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)  # getlist如果存在多个相同的值会把相同的值添加到一个列表中，[1,2]
            if not value_list:
                continue
            condition["{}__in".format(name)] = value_list
        """
        condition = {
            "status__in":[1, 2],
            "issues_type__in":[1,]
        }
        生成筛选条件后在把筛选条件传入下方的查询语句中
        """

        # 生成分页效果
        result = models.Issues.objects.filter(project_id=project_id).filter(**condition)
        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=result.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=5
        )
        #向数据库分片取数据
        issues_object_list = result[page_object.start:page_object.end]

        #FK筛选条件数据获取
        project_issues_type = models.IssuesType.objects.filter(project_id=project_id).values_list('id', 'title')

        #获取本项目所有参与用户提供select条件筛选
        project_user_list = [(request.tracer.project.creator_id, request.tracer.project.creator.username)]
        project_join_user = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id',
                                                                                                 'user__username')
        project_user_list.extend(project_join_user)
        # print(project_user_list)

        filter_list = [
            {'title': '问题类型', 'filter': CheckFilter("issues_type", project_issues_type, request)},
            {'title': '状态', 'filter': CheckFilter("status", models.Issues.status_choices, request)},
            {'title': '优先级', 'filter': CheckFilter("priority", models.Issues.priority_choices, request)},
            {'title': '指派者', 'filter': SelectFilter("assign", project_user_list, request)},
            {'title': '关注者', 'filter': SelectFilter("attention", project_user_list, request)},
        ]

        invite_form = ProjectInviteModelForm()

        return render(request, 'issues.html',
                      {"form": form,
                       "invite_form": invite_form,
                       "issues_object_list": issues_object_list,
                       "page_html": page_object.page_html(),
                       "filter_list": filter_list,
                       })

    # 如果是POST请求就检验前端提交的数据，检验成功提交数据库保存
    # print(request.POST)
    form = IssuesModelForm(request, data=request.POST)
    if form.is_valid():
        # print("检测完成")
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.save()
        # print("保存完成")
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})


def detail(request, project_id, issues_id):
    """编辑问题"""
    issues_object = models.Issues.objects.filter(project_id=project_id, id=issues_id).first()
    form = IssuesModelForm(request, instance=issues_object)
    return render(request, "issues_detail.html", {'form': form, 'issues_object': issues_object})


@csrf_exempt
def issues_record(request, project_id, issues_id):
    """操作记录初始化"""
    # print("aaa")
    if request.method == "GET":
        record_object = models.IssuesReply.objects.filter(issues_id=issues_id, issues__project_id=project_id)
        record_list = []
        for item in record_object:
            record_dict = {
                'id': item.id,
                'reply_type_text': item.get_reply_type_display(),
                'content': item.content,
                'creator': item.creator.username,
                'datetime': item.create_datetime.strftime("%Y-%m-%d %H:%M"),
                'reply_id': item.reply_id
            }
            record_list.append(record_dict)
        # print(record_list)
        return JsonResponse({"status": True, "data": record_list})

    form = IssuesReplyModelForm(data=request.POST)
    if form.is_valid():
        form.instance.reply_type = 2
        form.instance.issues_id = issues_id
        form.instance.creator = request.tracer.user
        instance = form.save()
        data_dict = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'reply_id': instance.reply_id
        }
        return JsonResponse({"status": True, "data": data_dict})
    return JsonResponse({'status': False, "error": form.errors})


@csrf_exempt
def issues_change(request, project_id, issues_id):
    """
    任务更新操作&任务更新操作记录生成
    获取前端传输过来的值格式需为：{'name': 'xxx', 'value': 'xxx'}
    """
    # 获取前端传输的值&数据库中相应的记录
    post_dict = json.loads(request.body.decode('utf-8'))
    issues_object = models.Issues.objects.filter(id=issues_id, project=request.tracer.project).first()
    print(post_dict)
    key = post_dict['name']
    value = post_dict['value']
    field_object = models.Issues._meta.get_field(key)
    print(field_object)

    # 接收验证后数据生成操作记录
    def create_reply_record(data):
        issues_reply_object = models.IssuesReply.objects.create(
            reply_type=1,
            issues_id=issues_id,
            content=data,
            creator=request.tracer.user,
        )
        change_dict = {
            'id': issues_reply_object.id,
            'reply_type_text': issues_reply_object.get_reply_type_display(),
            'content': issues_reply_object.content,
            'creator': issues_reply_object.creator.username,
            'datetime': issues_reply_object.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'reply_id': issues_reply_object.reply_id
        }

        return change_dict

    # 处理文本
    if key in ['subject', 'desc', 'start_date', 'end_date']:
        # print("进入文本验证")
        if not value:
            if not field_object.null:
                return JsonResponse({'status': False, 'error': '您选择的值不能为空'})
            setattr(issues_object, key, None)
            issues_object.save()
            change_record = '{} 更改为空'.format(field_object.verbose_name)
        else:
            setattr(issues_object, key, value)
            issues_object.save()
            change_record = '{} 更改为 {}'.format(field_object.verbose_name, value)
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})

    # 处理FK
    if key in ['issues_type', 'module', 'assign', 'parent']:
        if not value or len(value) == 0:
            # 字段不允许为空直接返回报错信息
            if not field_object.null:
                return JsonResponse({'status': False, 'error': '您选择的值不能为空'})
            # 字段允许为空保存操作记录并生成返回数据
            setattr(issues_object, key, None)
            issues_object.save()
            change_record = "{}更新为空".format(field_object.verbose_name)
        else:
            if key == "assign":
                if value == str(request.tracer.project.creator_id):
                    instance = request.tracer.project.creator
                else:
                    user_object = models.ProjectUser.objects.filter(project_id=project_id, user_id=value).first()
                    if not user_object:
                        return JsonResponse({'status': False, 'error': '您选择的值不存在'})
                    instance = user_object.user
                setattr(issues_object, key, instance)
                issues_object.save()
                # str(instance)获取类中__str__方法返回的值
                change_record = issues_reply_add = '{} 更改为 {}'.format(field_object.verbose_name, str(instance))
            else:
                # field_object.rel拿到field_object字段关联的对象
                instance = field_object.rel.model.objects.filter(id=value, project_id=project_id).first()
                # 条件判断是否是自己项目存在的FK
                if not instance:
                    return JsonResponse({'status': False, 'error': '您选择的值不存在'})
                setattr(issues_object, key, instance)
                issues_object.save()
                # str(instance)获取类中__str__方法返回的值
                change_record = issues_reply_add = '{} 更改为 {}'.format(field_object.verbose_name, str(instance))
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})

    # 处理choices
    if key in ['mode', 'status', 'priority']:
        selected_text = None
        for choices_id, choices_text in field_object.choices:
            if value == str(choices_id):
                selected_text = choices_text
                break
        if not selected_text:
            return JsonResponse({'status': False, 'error': '您选择的值不存在'})
        setattr(issues_object, key, value)
        issues_object.save()
        change_record = '{} 更改为 {}'.format(field_object.verbose_name, selected_text)
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})

    # 处理m2m
    if key == "attention":
        if not value:
            change_record = '{} 更改为空'.format(field_object.verbose_name)
        else:
            user_dict = {str(request.tracer.project.creator_id): request.tracer.project.creator.username, }
            project_user_list = models.ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_list:
                user_dict[str(item.user_id)] = item.user.username
            username_list = []
            for user_id in value:
                username = user_dict[str(user_id)]
                if not username:
                    return JsonResponse({'status': False, 'error': '用户不存在请重新设置'})
            issues_object.attention.set(value)  # 设置数据库FK可多选的值，value是列表类型
            issues_object.save()
            change_record = '{} 更改为 {}'.format(field_object.verbose_name, ','.join(value))
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})

    return JsonResponse({})


def invite_url(request, project_id):
    """生成邀请码"""
    form = ProjectInviteModelForm(data=request.POST)
    if form.is_valid():
        """
        1、验证是否有权限创建验证码
        2、创建验证码
        3、把验证码保存到数据库
        4、生成邀请码链接并返回给前端
        """
        if request.tracer.project.creator != request.tracer.user:
            form.add_error('period', '你不是项目创建者，无权创建邀请码')
            return JsonResponse({'status': False, 'error': form.errors})

        random_invite_code = uid(request.tracer.user.phone)
        print(random_invite_code)
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.instance.code = random_invite_code
        form.save()
        """
        将邀请链接返回给前端
        """
        url = "{scheme}://{host}{path}".format(
            scheme=request.scheme,
            host=request.get_host(),
            path=reverse('invite_join', kwargs={'code': random_invite_code})
        )
        return JsonResponse({'status': True, 'data': url})
    return JsonResponse({'status': False, 'error': form.errors})


def invite_join(request, code):
    """验证邀请码"""
    if request.tracer:
        code_object = models.ProjectInvite.objects.filter(code=code).first()
        if not code_object:
            return JsonResponse({'status': True, 'error': '未查询到此验证码'})

        if request.tracer.user.id == code_object.creator_id:
            return JsonResponse({'status': True, 'error': '您是此邀请码的创建者！'})

        project_user = models.ProjectUser.objects.filter(project=code_object.project, user=request.tracer.user).first()
        if project_user:
            return JsonResponse({'status': False, 'error': project_user})
        project_invite = ProjectUser(user=request.tracer.user, project=code_object.project, invitee=code_object.creator)
        project_invite.save()
        return HttpResponseRedirect('/project/list/')
    return HttpResponseRedirect('/login/')
