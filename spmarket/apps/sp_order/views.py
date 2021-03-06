from datetime import datetime
import os
from alipay import AliPay
from django.conf import settings
import time
import random

from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from sp_goods.models import GoodsSku
from sp_order.models import Transport, Order, OrderGoods
from sp_user.helper import verify_login
from sp_user.models import SpAddress


class TrueOrderView(View):
    def get(self, request):
        user_id = request.session.get("ID")
        if user_id is None:
            return redirect("sp_user:login")

        # 获得当前用户收货地址
        address = SpAddress.objects.filter(isDelete=False, user_id=user_id).order_by("-isDefault").first()
        # 获得订单信息
        sku_ids = request.GET.getlist("sku_id")
        if len(sku_ids) == 0:
            return redirect("sp_cart:index")
        goodsskus = []
        r = get_redis_connection("default")
        cart_key = "cart_key_{}".format(user_id)
        total_price = 0

        for sku_id in sku_ids:
            try:
                sku_id = int(sku_id)
            except:
                return redirect("sp_cart:index")
            goodssku = GoodsSku.objects.get(pk=sku_id)
            count = r.hget(cart_key, sku_id)
            count = int(count)
            goodssku.count = count
            # 计算商品总价格
            total_price += goodssku.price * count
            # 添加商品到列表中
            goodsskus.append(goodssku)

        # 处理运输方式
        transports = Transport.objects.filter(isDelete=False).order_by("price")
        # 将地址渲染到页面
        context = {
            "address": address,
            "goodsskus": goodsskus,
            "total_price": total_price,
            "transports": transports,
        }
        return render(request, 'sp_order/tureorder.html', context)

    def post(self, request):
        # 判断用户是否登录
        user_id = request.session.get("ID")
        if user_id is None:
            return JsonResponse({"code": 1, "errmsg": "没有登录!"})
        # 接收参数
        address_id = request.POST.get("address_id")
        sku_ids = request.POST.getlist("sku_id")
        transport = request.POST.get("transport")
        # 判断参数的合法性
        if not all([address_id, sku_ids, transport]):
            return JsonResponse({"code": 2, "errmsg": "参数错误!"})
        # 判断传入参数是否为整数
        try:
            address_id = int(address_id)
            transport = int(transport)
            sku_ids_int = [int(sku_id) for sku_id in sku_ids]
        except:
            return JsonResponse({"code": 3, "errmsg": "参数错误!"})
        # 判断收货地址
        try:
            address = SpAddress.objects.get(pk=address_id, isDelete=False)
        except SpAddress.DoesNotExist:
            return JsonResponse({"code": 4, "errmsg": "收货地址不存在!"})
        # 判断运输方式
        try:
            trans = Transport.objects.get(pk=transport, isDelete=False)
        except Transport.DoesNotExist:
            return JsonResponse({"code": 5, "errmsg": "运输方式不存在!"})
        # 保存订单基本信息表
        order_sn = "{}{}{}".format(datetime.now().strftime("%Y%m%d%H%M%S"), user_id, random.randint(10000, 99999))
        # 准备详细地址
        address_detail = "{}{}{}-{}".format(address.hcity, address.hproper, address.harea, address.detail)

        # 返回的订单基本信息对象
        order = Order.objects.create(
            order_sn=order_sn,
            user_id=user_id,
            username=address.username,
            phone=address.phone,
            address=address_detail,
            transport=trans.name,
            transport_price=trans.price
        )

        # 连接redis
        r = get_redis_connection("default")
        # 准备key
        cart_key = "cart_key_{}".format(user_id)

        # 先保存订单商品表
        # 准备个变量保存商品总价格
        order_amount = 0

        # 遍历商品的id
        for sku_id in sku_ids_int:
            # 保存商品到订单商品表
            # 保证商品也得存在
            try:
                goodssku = GoodsSku.objects.get(pk=sku_id, isDelete=False, is_on_sale=True)
            except GoodsSku.DoesNotExist:
                # 商品不存在
                return JsonResponse({"code": 6, "errmsg": "商品不存在!"})
            # 获取购物车中的数量
            count = r.hget(cart_key, sku_id)
            count = int(count)
            # 保证库存足够
            if goodssku.stock < count:
                return JsonResponse({"code": 7, "errmsg": "商品库存不足!"})
            # 保存订单商品表
            OrderGoods.objects.create(
                order=order,
                goods_sku=goodssku,
                price=goodssku.price,
                count=count
            )
            # 销量增加
            goodssku.sales += count
            # 库存减少
            goodssku.stock -= count
            # 保存
            goodssku.save()
            # 统计总价格
            order_amount += goodssku.price * count
        try:
            order.order_amount = order_amount
            order.save()
        except:
            return JsonResponse({"code": 8, "errmsg": "保存商品总金额失败!"})

        # 所有都成功, 删除购物车中的数据
        r.hdel(cart_key, *sku_ids_int)
        # 成功后跳转确认支付页面
        return JsonResponse({"code": 0, "msg": "创建订单成功!", "order_sn": order_sn})


class OrderView(View):
    def get(self, request):
        # 接收用户id
        user_id = request.session.get("ID")
        # 接收order_sn
        order_sn = request.GET.get("order_sn")

        try:
            order = Order.objects.get(order_sn=order_sn,user_id=user_id)
        except Order.DoesNotExist:
            return redirect("sp_cart:index")


        # 计算订单总金额
        total = order.order_amount + order.transport_price
        # 渲染订单到页面
        context = {
            "order":order,
            "total":total,
        }
        return render(request, 'sp_order/order.html',context)

    def post(self, request):
        pass

@verify_login
def pay(request):
    # 接收请求中order_sn
    order_sn = request.GET.get("order_sn")
    if order_sn is None:
        return redirect("sp_goods:首页")

    user_id = request.session.get("ID")
    # 查询订单信息
    try:
        order = Order.objects.get(order_sn=order_sn, user_id=user_id, status=0)
    except Order.DoesNotExist:
        return redirect("sp_goods:首页")

    # 订单总金额
    total = order.order_amount + order.transport_price

    # 订单描述
    brief = "最low商城支付"

    # 发起支付, 生成了一个地址, 跳转到支付宝地址上
    app_private_key_string = open(os.path.join(settings.BASE_DIR, "apps/sp_order/private_key.txt")).read()
    alipay_public_key_string = open(os.path.join(settings.BASE_DIR, "apps/sp_order/ali_public_key.txt")).read()

    # 创建对象
    alipay = AliPay(
        appid="2016092300575801",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 发起支付
    # 手机网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order.order_sn,  # 订单号
        total_amount=str(total),  # 总金额
        subject=brief,
        return_url="http://127.0.0.1:8000/order/success/",
        notify_url=None  # 可选, 不填则使用默认notify url
    )

    # 跳转到支付链接
    # return HttpResponse("https://openapi.alipaydev.com/gateway.do?{}".format(order_string))
    return redirect("https://openapi.alipaydev.com/gateway.do?{}".format(order_string))


@verify_login
def success(request):
     # 发起一次支付查询,查看是否支付成功
    # 发起支付, 生成了一个地址, 跳转到支付宝地址上
    app_private_key_string = open(os.path.join(settings.BASE_DIR, "apps/sp_order/private_key.txt")).read()
    alipay_public_key_string = open(os.path.join(settings.BASE_DIR, "apps/sp_order/ali_public_key.txt")).read()

    # 创建对象
    alipay = AliPay(
        appid="2016092300577098",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 获取参数
    out_trade_no = request.GET.get('out_trade_no')

    # check order status
    paid = False
    for i in range(3):
        result = alipay.api_alipay_trade_query(out_trade_no=out_trade_no)
        if result.get("trade_status", "") == "TRADE_SUCCESS":
            paid = True
            break
        else:
            time.sleep(3)

    if paid is False:
        context = {
            "message": "支付失败"
        }
    else:
        # 支付成功
        # 修改状态
        user_id = request.session.get("ID")
        Order.objects.filter(order_sn=out_trade_no, user_id=user_id, status=0).update(status=1)

        # 渲染数据
        context = {
            "message": "支付成功"
        }

    # 支付成功之后返回的页面
    return render(request, 'sp_order/pay.html', context)
