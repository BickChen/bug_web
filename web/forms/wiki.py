from django import forms
from web import models
from Tool.local_tool.bootstrap import BootStrapForm


class WikiModelForm(BootStrapForm, forms.ModelForm):

    class Meta:
        model = models.Wiki
        exclude = ['project', 'depth']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        total_data_list = [("", "请选择"), ]
        data_list = models.Wiki.objects.filter(project=request.tracer.project).values_list('id', 'title')
        total_data_list.extend(data_list)
        #找到想要的字段把它绑定显示的数据重制
        self.fields['parent'].choices = total_data_list
