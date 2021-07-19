from django import forms
from web import models
from Tool.local_tool.bootstrap import BootStrapForm
from django.core.exceptions import ValidationError


class IssuesModelForm(BootStrapForm, forms.ModelForm):

    class Meta:
        model = models.Issues
        exclude = ['project', 'creator', 'create_datetime', 'latest_update_datetime']
        widgets = {
            "issues_type": forms.Select(attrs={'class': "selectpicker"}),
            "module": forms.Select(attrs={'class': "selectpicker"}),
            "priority": forms.Select(attrs={'class': "selectpicker"}),
            "status": forms.Select(attrs={'class': "selectpicker"}),
            "assign": forms.Select(attrs={'class': "selectpicker", "data-live-search": 'true'}),
            #SelectMultiple参数代表可以多选
            "attention": forms.SelectMultiple(attrs={'class': "selectpicker", "data-live-search": 'true', "data-actions-box": "true"}),
            "mode": forms.Select(attrs={'class': "selectpicker"}),
            "parent": forms.Select(attrs={'class': "selectpicker", "data-live-search": 'true'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        #数据初始化，只能显示当前项目所创建的数据
        #重写类型数据
        #1、获取所有的当前项目的所有问题类型
        type_list = models.IssuesType.objects.filter(project=request.tracer.project).values_list('id', 'title')
        #print(type_list)
        self.fields['issues_type'].choices = type_list
        #重写当前项目所有模块数据
        #1、获取当前项目所有的模块
        model_list = [("", "无")]
        model_list.extend(models.Module.objects.filter(project=request.tracer.project).values_list('id', 'title'))
        #print(model_list)
        self.fields['module'].choices = model_list
        #重写当前指派者&关注者
        project_user_list = [(request.tracer.user.id, request.tracer.user.username)]
        project_user_list.extend(models.ProjectUser.objects.filter(project=request.tracer.project).values_list("user_id", "user__username"))
        project_list = [('', '无'), (request.tracer.user.id, request.tracer.user.username)]
        project_list.extend(
            models.ProjectUser.objects.filter(project=request.tracer.project).values_list("user_id", "user__username"))
        #print(project_user_list)
        self.fields['assign'].choices = project_list
        self.fields['attention'].choices = project_user_list
        #重写当前项目所有父问题
        parent_list = [("", "无")]
        parent_list.extend(models.Issues.objects.filter(project=request.tracer.project).values_list('id', 'subject'))
        #print(parent_list)
        self.fields['parent'].choices = parent_list





    def clean_subject(self):
        issues_name = self.cleaned_data['subject']
        issues_object = models.Issues.objects.filter(project=self.request.tracer.project, subject=issues_name).first()
        if issues_object:
            raise ValidationError('任务已存在')
        return issues_name


class IssuesReplyModelForm(forms.ModelForm):
    class Meta:
        model = models.IssuesReply
        fields = ['content', 'reply']


class ProjectInviteModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.ProjectInvite
        fields = ['period', 'count']
