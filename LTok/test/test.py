#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
================================================================================
    Author: Last_D
    Created Time: 2014-10-14 13:07:09 Tue
    Last Modified: 2014-10-14 23:53:44 Tue
    Description:
        Desired coding style.
    Change Activity:
        - None
================================================================================
"""
import logging
logging.basicConfig(level=logging.INFO)

from web_dead import App, template, get, ctx

# 首页
@get('/index')
def index():
    """Test my web framework..."""
    request = ctx.request
    L = [request.path_info, request.request_method]
    return template.render('index.html', info_list = L)

app = App(__file__)
# 添加路径信息, 也可以从模块批量导入url add_module(module_name)
app.add_url(index)
if __name__ == '__main__':
    app.run()
