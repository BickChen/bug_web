from django.db import models
# Create your models here.


class UserInfo(models.Model):
    username = models.CharField(verbose_name='用户名', max_length=32, null=False, db_index=True)
    email = models.EmailField(verbose_name='邮箱', max_length=32, null=True)
    phone = models.CharField(verbose_name='手机号', max_length=11, null=False, unique=True)
    password = models.CharField(verbose_name='密码', max_length=64, null=True)

    def __str__(self):
        return self.username


class PricePolicy(models.Model):
    category_choices = (
        (1, '免费版'),
        (2, '收费版'),
        (3, '其他'),
    )
    category = models.SmallIntegerField(verbose_name='收费类型', default=2, choices=category_choices)
    title = models.CharField(verbose_name='标题', max_length=32, null=False, unique=True)
    price = models.PositiveIntegerField(verbose_name='价格')
    project_num = models.PositiveIntegerField(verbose_name='项目数')
    project_member = models.PositiveIntegerField(verbose_name='项目成员数')
    project_space = models.PositiveIntegerField(verbose_name='单项目可用空间(G)')
    per_file_size = models.PositiveIntegerField(verbose_name='单文件上传大小(M)')
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Transaction(models.Model):
    status_choice = (
        (1, '未支付'),
        (2, '已支付')
    )

    status = models.SmallIntegerField(verbose_name='状态', choices=status_choice)
    order = models.CharField(verbose_name='订单号', max_length=64, unique=True)
    user = models.ForeignKey(verbose_name='用户', to='UserInfo')
    price_policy = models.ForeignKey(verbose_name='价格策略', to='PricePolicy')
    count = models.IntegerField(verbose_name='数量(年)', help_text='0代表无限期')
    price = models.IntegerField(verbose_name='实际支付价格',)

    start_datetime = models.DateTimeField(verbose_name='开始时间', null=True, blank=True)
    end_datetime = models.DateTimeField(verbose_name='结束时间', null=True, blank=True)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Project(models.Model):

    COLOR_CHOICES = (
        (1, '#56b8eb'),
        (2, '#f28033'),
        (3, '#ebc656'),
        (4, '#a2d148'),
        (5, '#20BFA4'),
        (6, '#7461c2'),
        (7, '#20bfa3')
    )
    name = models.CharField(verbose_name='项目名', max_length=32)
    color = models.SmallIntegerField(verbose_name='颜色', choices=COLOR_CHOICES, default=1)
    desc = models.CharField(verbose_name='项目描述', max_length=255, null=True, blank=True)
    use_space = models.BigIntegerField(verbose_name="项目已使用空间", default=0, help_text="字节")
    star = models.BooleanField(verbose_name='星标', default=False)

    bucket = models.CharField(verbose_name='腾讯对象存储桶', max_length=128, null=True)
    region = models.CharField(verbose_name='腾讯对象存储桶区域', max_length=32, null=True)

    join_count = models.SmallIntegerField(verbose_name='参与人数', default=1)
    creator = models.ForeignKey(verbose_name="创建者", to='UserInfo')
    creator_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class ProjectUser(models.Model):
    user = models.ForeignKey(verbose_name='用户', to="UserInfo", related_name='progects')
    project = models.ForeignKey(verbose_name='项目', to="Project")
    invitee = models.ForeignKey(verbose_name='邀请者', to="UserInfo", related_name='invites', null=True, blank=True)
    star = models.BooleanField(verbose_name='星标', default=False)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Wiki(models.Model):
    title = models.CharField(verbose_name='标题', max_length=32)
    content = models.TextField(verbose_name='内容')
    project = models.ForeignKey(verbose_name='项目', to="Project")
    parent = models.ForeignKey(verbose_name='父文章', to='Wiki', null=True, blank=True, related_name='children')
    depth = models.IntegerField(verbose_name='深度', default=1)

    def __str__(self):
        return self.title


class FileRepository(models.Model):
    """文件库"""
    file_type_choices = (
        (1, '文件'),
        (2, '文件夹'),
    )
    project = models.ForeignKey(verbose_name='项目', to="Project")
    name = models.CharField(verbose_name="文件夹名", max_length=64, help_text="文件/文件夹名")
    key = models.CharField(verbose_name='关联COS文件名', max_length=128, null=True, blank=True)
    file_type = models.SmallIntegerField(verbose_name='文件类型', choices=file_type_choices)
    file_size = models.BigIntegerField(verbose_name='文件大小', null=True, blank=True, help_text="字节")
    file_path = models.CharField(verbose_name='文件路径', max_length=255, null=True, blank=True)
    parent = models.ForeignKey(verbose_name='父目录', to='self', related_name='child', null=True, blank=True)
    updata_user = models.ForeignKey(verbose_name='更新者', to=UserInfo)
    updata_datatime = models.DateTimeField(verbose_name='更新时间', auto_now=True)


class Module(models.Model):
    """模块表"""
    project = models.ForeignKey(verbose_name="项目", to="Project")
    title = models.CharField(verbose_name="模块名称", max_length=64)

    def __str__(self):
        return self.title


class IssuesType(models.Model):
    project = models.ForeignKey(verbose_name="项目", to="Project")
    title = models.CharField(verbose_name="类型名称", max_length=64)

    def __str__(self):
        return self.title


class Issues(models.Model):
    project = models.ForeignKey(verbose_name="项目", to="Project")
    issues_type = models.ForeignKey(verbose_name="类型", to="IssuesType")
    module = models.ForeignKey(verbose_name="模块", to="Module", null=True, blank=True)

    subject = models.CharField(verbose_name="主题", max_length=80)
    desc = models.TextField(verbose_name="问题描述")

    priority_choices = (
        ("danger", "高"),
        ("warning", "中"),
        ("success", "低"),
    )
    priority = models.CharField(verbose_name="优先级", max_length=12, choices=priority_choices, default="danger")

    status_choices = (
        (1, '新建'),
        (2, '正在处理'),
        (3, '已解决'),
        (4, '已忽略'),
        (5, '带反馈'),
        (6, '已关闭'),
        (7, '重新开始'),
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)

    assign = models.ForeignKey(verbose_name="指派者", to="UserInfo", related_name="task", null=True, blank=True)
    attention = models.ManyToManyField(verbose_name="关注者", to="UserInfo", related_name="observe", null=True, blank=True)
    start_date = models.DateField(verbose_name="开始时间", null=True, blank=True)
    end_date = models.DateField(verbose_name="结束时间", null=True, blank=True)

    mode_choices = (
        (1, "公开模式"),
        (2, "隐私模式")
    )
    mode = models.SmallIntegerField(verbose_name="模式", choices=mode_choices, default=1)
    parent = models.ForeignKey(verbose_name="父任务", to="self", related_name="child", null=True, blank=True, on_delete=models.SET_NULL)
    creator = models.ForeignKey(verbose_name="创建者", to="UserInfo", related_name="create_problems")
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    latest_update_datetime = models.DateTimeField(verbose_name="最后更新时间", auto_now=True)

    def __str__(self):
        return self.subject


class IssuesReply(models.Model):
    """任务回复评论表"""

    reply_type_choices = (
        (1, '修改记录'),
        (2, '回复')
    )

    reply_type = models.IntegerField(verbose_name="类型", choices=reply_type_choices)
    issues = models.ForeignKey(verbose_name="问题", to="Issues")
    content = models.TextField(verbose_name="描述")
    creator = models.ForeignKey(verbose_name="创建者", to="UserInfo", related_name="create_reply")
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    reply = models.ForeignKey(verbose_name="回复", to="self", null=True, blank=True)


class ProjectInvite(models.Model):
    """项目邀请码表"""
    project = models.ForeignKey(verbose_name="项目", to='Project')
    code = models.CharField(verbose_name='邀请码', max_length=128, unique=True)
    count = models.PositiveIntegerField(verbose_name='限制数量', null=True, blank=True, help_text='空表示不限制数量')
    use_count = models.PositiveIntegerField(verbose_name='已邀请数量', default=0)
    period_choices = (
        (30, "30分钟"),
        (60, "1小时"),
        (300, "5小时"),
        (1440, "24小时"),
    )
    period = models.IntegerField(verbose_name="有效期", choices=period_choices, default=1440)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    creator = models.ForeignKey(verbose_name='创建者', to="UserInfo", related_name='create_invite')
