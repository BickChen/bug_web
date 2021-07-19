from django import forms
from Tool.local_tool.bootstrap import BootStrapForm
from web import models
from django.core.validators import ValidationError
from web.forms.widgets import ColorRadioSelect


class ProjectModelForm(BootStrapForm, forms.ModelForm):

    bootstrap_class_exclude = ['color']

    class Meta:
        model = models.Project
        fields = ['name', 'color', 'desc']
        widgets = {
            'desc': forms.Textarea,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        #项目重名校验
        #print('进入验证')
        name = self.cleaned_data['name']
        #print(name)

        exists = models.Project.objects.filter(name=name, creator=self.request.tracer.user).exists()
        #print(exists)
        if exists:
            raise ValidationError('当前项目已存在')
        #当前用户是否还有额度创建项目

        count = models.Project.objects.filter(creator=self.request.tracer.user).count()
        #print(count)
        if count >= self.request.tracer.price_policy.project_num:
            raise ValidationError('项目个数超限，请购买付费套餐')

        return name