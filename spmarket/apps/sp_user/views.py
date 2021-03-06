import random
import re
import uuid

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django_redis import get_redis_connection

from db.base_view import BaseVerifyView
from sp_user.forms import RegModelForm, LoginModelForm, ForgetModelForm, AddressModelForm, EditAddressModelForm
from sp_user.helper import login, send_sms
from sp_user.models import SpUser, SpAddress


# 注册
class RegView(View):
    def get(self, request):
        return render(request, 'sp_user/reg.html')

    def post(self, request):
        # 1. 接收
        data = request.POST
        # 2. 处理
        form = RegModelForm(data)
        if form.is_valid():
            data = form.cleaned_data
            phone = data.get("phone")
            password = data.get('password2')
            SpUser.objects.create(phone=phone, password=password)
            return redirect("sp_user:login")
        else:
            context = {
                "errors": form.errors,
            }
            # 3. 响应
            return render(request, "sp_user/reg.html", context)


# 登录
class LoginView(View):
    def get(self, request):
        login_form = LoginModelForm()
        return render(request, 'sp_user/login.html')

    def post(self, request):
        # 接收数据
        data = request.POST
        # 验证数据
        login_form = LoginModelForm(data)
        if login_form.is_valid():
            # 验证成功后将登陆标识放到session中
            user = login_form.cleaned_data.get('user')
            # 调用登陆的方法,放在helper模块中的
            login(request, user)
            # 跳转到用户中心页面
            next = request.GET.get('next')
            if next:
                return redirect(next)
            else:
                return redirect('sp_user:member')
        else:
            return render(request, "sp_user/login.html", {'form': login_form})


# 找回密码
class ForgetPassView(View):

    def get(self, request):
        return render(request, 'sp_user/forgetpassword.html')

    def post(self, request):
        # 1. 接收
        data = request.POST
        # 2. 处理
        form = ForgetModelForm(data)
        if form.is_valid():
            data = form.cleaned_data
            phone = data.get("phone")
            password = data.get('password2')
            SpUser.objects.filter(phone=phone).update(password=password)
            return redirect("sp_user:login")
        else:
            context = {
                "errors": form.errors,
            }
            # 3. 响应
            return render(request, "sp_user/reg.html", context)


# 个人中心
class MemeberView(View):

    def get(self, request):
        context = {
            "phone": request.session.get('phone'),
            "head": request.session.get('head'),
        }
        return render(request, 'sp_user/member.html', context)

    def post(self, request):
        pass


# 个人资料
class InfoView(View):

    def get(self, request):
        user_id = request.session.get("ID")
        user = SpUser.objects.get(pk=user_id)
        context = {
            "user": user
        }
        return render(request, 'sp_user/infor.html', context)

    def post(self, request):
        user_id = request.session.get("ID")
        user = SpUser.objects.get(pk=user_id)
        user.nickname = request.POST.get("nickname")
        user.gender = request.POST.get("gender")
        user.birth_of_date = request.POST.get("birth_of_date")
        user.school_name = request.POST.get("school_name")
        user.hometown = request.POST.get("hometown")
        user.address = request.POST.get("address")
        user.head = request.FILES.get("head")
        user.save()
        login(request, user)
        return redirect("sp_user:member")


# 短信验证

def send_msg_phone(request):
    if request.method == 'POST':
        phone = request.POST.get("phone", "")
        # 验证手机号码格式是否正确
        phone_re = re.compile("^1[3-9]\d{9}$")
        # 匹配传入的手机号码
        rs = re.search(phone_re, phone)
        if rs is None:
            return JsonResponse({"err": 1, "errmsg": "手机号码格式错误!"})
        # 生成随机码 随机数字组成
        random_code = "".join([str(random.randint(0, 9)) for _ in range(4)])
        # 保存随机码到redis中
        r = get_redis_connection("default")
        # 直接开始操作
        r.set(phone, random_code)
        # 设置过期时间
        r.expire(phone, 120)
        # 使用阿里发送短信
        # __business_id = uuid.uuid1()
        # params = "{\"code\":\"%s\",\"product\":\"BY爸爸的商城\"}" % random_code
        # print(send_sms(__business_id, phone, "注册验证", "SMS_2245271", params))

        print(random_code)
        return JsonResponse({"err": 0})
    else:
        # 请求错误,就显示提示信息
        return JsonResponse({"err": 1, "errmsg": "请求方式错误"})


# 收货地址
class AddressView(BaseVerifyView):
    def get(self, request):
        user_id = request.session.get("ID")
        addresses = SpAddress.objects.filter(user_id=user_id, isDelete=False).order_by("-isDefault")
        context = {
            'addresses': addresses
        }
        return render(request, 'sp_user/gladdress.html', context)

    def post(self, request):
        pass


# 添加收货地址
class AddAddressView(BaseVerifyView):
    def get(self, request):
        return render(request, 'sp_user/address.html')

    def post(self, request):
        data = request.POST.dict()
        data['user_id'] = request.session.get("ID")
        form = AddressModelForm(data)
        if form.is_valid():
            form.instance.user_id = request.session.get("ID")
            form.save()
            return redirect("sp_user:address")
        else:
            context = {
                "form": form
            }
        return render(request, 'sp_user/address.html', context)


# 修改收货地址
class EditAddressView(BaseVerifyView):
    def get(self, request, id):
        user_id = request.session.get("ID")
        try:
            address = SpAddress.objects.get(user_id=user_id, pk=id)
        except SpAddress.DoesNotExist:
            return redirect("sp_user:address")
        context = {
            "address": address
        }
        return render(request, 'sp_user/address-edit.html', context)

    def post(self, request, id):
        data = request.POST.dict()
        user_id = request.session.get("ID")
        data['user_id'] = user_id
        form = EditAddressModelForm(data)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            id = data.get('id')
            SpAddress.objects.filter(user_id=user_id, pk=id).update(**cleaned_data)
            return redirect("sp_user:address")
        else:
            context = {
                "form": form,
                "address": data
            }
            return render(request, 'sp_user/address.html', context)


# 删除地址

def delAddress(request):
    if request.method == 'POST':
        user_id = request.session.get("ID")
        id = request.POST.get("id")
        if user_id is None:
            return JsonResponse({"code": 1, "errmsg": "没有登陆!"})
        SpAddress.objects.filter(user_id=user_id, pk=id).update(isDelete=True)
        return JsonResponse({"code": 0})
    else:
        return JsonResponse({"code": 2, "errmsg": "请求方式错误"})


# 设置默认值
def defAddress(request):
    if request.method == 'POST':
        user_id = request.session.get("ID")
        id = request.POST.get("id")
        if user_id is None:
            return JsonResponse({"code": 1, "errmsg": "没有登陆!"})
        SpAddress.objects.update(isDefault = False)
        SpAddress.objects.filter(user_id=user_id, pk=id).update(isDefault=True)
        return JsonResponse({"code": 0})
    else:
        return JsonResponse({"code": 2, "errmsg": "请求方式错误"})


# 全部订单

class AllorderView(View):

    def get(self, request):
        return render(request, 'sp_user/allorder.html')

    def post(self, request):
        pass
