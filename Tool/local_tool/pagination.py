"""
分页功能模块说明：

"""


class Pagination(object):
    def __init__(self, current_page, all_count, base_url, query_params, per_page=30, pager_page_count=11):
        """
        :param current_page: 当前页码
        :param all_count: 数据库中总条数(int)
        :param base_url: 基础URL
        :param query_params: queryDict对象，内部包含所有当前URL的原条件
        :param per_page: 每页显示数据条数(int)
        :param pager_page_count: 页面上最多显示的页码数量
        """
        #获取基础URL：例如http://127.0.0.1/abc/1/abc/P:xx&P:xx获取http://127.0.0.1/abc/1/abc/
        self.base_url = base_url
        #将获取到的页码值转化为int类型方便对比，如果传入的页码不是数字类型默认值设置为1
        try:
            self.current_page = int(current_page)
            if self.current_page <= 0:
                self.current_page = 1
        except Exception as e:
            self.current_page = 1
        #copy方法浅拷贝request.GET传进来的值
        query_params = query_params.copy()
        query_params._mutable = True

        self.query_params = query_params
        self.per_page = per_page
        self.all_count = all_count
        self.pager_page_count = pager_page_count
        #算出总共的页码数
        pager_count, b = divmod(all_count, per_page)
        if b != 0:
            pager_count += 1
        self.pager_count = pager_count
        #算出页面上最多显示的页码数的一半
        half_pager_page_count = int(pager_page_count / 2)
        self.half_pager_page_count = half_pager_page_count

    #property装饰器把一个方法变成一个属性，另外可以提供数据校验效果

    @property
    def start(self):
        """
        数据获取值起始索引
        :return:
        """
        return (self.current_page - 1) * self.per_page

    @property
    def end(self):
        """
        数据获取值结束索引
        :return:
        """
        return self.current_page * self.per_page

    def page_html(self):
        """
        生成HTML页码
        :return:
        """

        if self.all_count == 0:
            return ""

        #如果数据总页码Pager_count < 最大显示页码数pager_page_count
        if self.pager_count < self.pager_page_count:
            pager_start = 1
            pager_end = self.pager_count
        else:
            #如果数据页码已经超过11
            #判断： 如果当前页数　<= 总页码半数half_pager_page_count
            if self.current_page <= self.half_pager_page_count:
                pager_start = 1
                pager_end = self.pager_page_count
            else:
                # 如果：当前页+最多显示页码的半数 > 总页码
                if (self.current_page + self.half_pager_page_count) > self.pager_count:
                    #起始页码就等于总页码减去最大显示页码例如：显示页码为11，总页码为13，当当前页是6的时候
                    # 6+(13/2)=12 12大于11显示起始页就应该是 13-11+1 = 3起始显示页码就为3
                    pager_start = self.pager_count - self.pager_page_count + 1
                    pager_end = self.pager_count
                else:
                    #如果：当前页 + 最多显示页码的半数 > 总页码
                    #起始页的位置就应该是5 - 5 = 0
                    #结束页的位置就应该是5 + 5 = 10
                    pager_start = self.current_page - self.half_pager_page_count
                    pager_end = self.current_page + self.half_pager_page_count

        #创建生成分页列表
        page_list = []
        #如果起始页为1的话，那么上一页按钮跳转值为#否则为当前页-1
        if self.current_page <= 1:
            prev = "<li><a href='#'>上一页</a></li>"
        else:
            self.query_params['page'] = self.current_page -1
            prev = "<li><a href='%s?%s'>上一页</a></li>"%(self.base_url, self.query_params.urlencode())
        page_list.append(prev)
        #判断循环的页码是否为当前页码，为当前页码则加上active选中属性
        for i in range(pager_start, pager_end + 1):
            self.query_params['page'] = i
            if self.current_page == i:
                tpl = "<li class='active'><a href='%s?%s'>%s</a></li>"%(self.base_url, self.query_params.urlencode(), i)
            else:
                tpl = "<li><a href='%s?%s'>%s</a></li>" % (
                self.base_url, self.query_params.urlencode(), i)
            page_list.append(tpl)

        if self.current_page >= self.pager_count:
            nex = "<li><a href='#'>下一页</a></li>"
        else:
            self.query_params['page'] = self.current_page + 1
            nex = "<li><a href='%s?%s'>下一页</a></li>"%(self.base_url, self.query_params.urlencode(),)
        page_list.append(nex)

        if self.all_count:
            tpl = "<li class='disabled'><a>共%s条数据，页码%s/%s页</a></li>"%(self.all_count, self.current_page, self.pager_count,)
            page_list.append(tpl)
        #将生成好的数据拼接成字符串的形式返回给前端
        page_str = "".join(page_list)
        return page_str

