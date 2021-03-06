from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

# Create your models here.

is_on_sale_choices = (
    (0, "下架"),
    (1, "上架"),
)

# 商品分类表
class GoodsClass(models.Model):
    ClassName = models.CharField(max_length=50,
                                 verbose_name='分类名'
                                 )
    ClassIntro = models.CharField(max_length=255,
                                  null=True,
                                  blank=True,
                                  verbose_name='分类简介'
                                  )
    add_time = models.DateTimeField(auto_now_add=True,
                                    verbose_name="添加时间"
                                    )
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间"
                                       )
    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        db_table = "goods_class"
        verbose_name = "商品分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.ClassName


# 商品spu表
class GoodsSpu(models.Model):
    SpuName = models.CharField(max_length=50,
                               verbose_name='spu名称'
                               )
    SpuIntro = RichTextUploadingField(verbose_name="商品详情")

    class Meta:
        db_table = "goods_spu"
        verbose_name = "商品spu"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SpuName


# 商品sku表
class GoodsSku(models.Model):
    unit_choices = (
        (1, "箱"),
        (2, "斤"),
        (3, "个"),
        (4,"台"),
    )
    spu_id = models.ForeignKey(to="GoodsSpu",
                               verbose_name="商品spu"
                               )
    sku_name = models.CharField(max_length=50,
                                verbose_name="商品名"
                                )
    desc = models.CharField(max_length=100,
                            null=True,
                            blank=True,
                            verbose_name="简介"
                            )
    price = models.DecimalField(max_digits=9,
                                decimal_places=2,
                                default=0,
                                verbose_name="价格"
                                )
    unit = models.SmallIntegerField(choices=unit_choices,
                                    default=3,
                                    verbose_name="单位"
                                    )
    stock = models.IntegerField(verbose_name="库存",
                                default=0
                                )
    sales = models.IntegerField(verbose_name="销量",
                                default=0
                                )
    url = models.ImageField(verbose_name='封面图片',
                            upload_to='goods/%Y%m/%d'
                            )
    is_on_sale = models.BooleanField(verbose_name="是否上架",
                                     choices=is_on_sale_choices,
                                     default=0
                                     )
    category_id = models.ForeignKey(to="GoodsClass",
                                    verbose_name="商品分类id"
                                    )
    add_time = models.DateTimeField(auto_now_add=True,
                                    verbose_name="添加时间"
                                    )
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间"
                                       )
    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        verbose_name = "商品sku"
        verbose_name_plural = verbose_name
        db_table = "goods_sku"

    def __str__(self):
        return self.sku_name


# 商品相册
class GoodsImg(models.Model):
    url = models.ImageField(verbose_name="相册图片地址",
                            upload_to='goods_gallery/%Y%m/%d'
                            )
    sku_id = models.ForeignKey(to="GoodsSku",
                               verbose_name="商品sku id"
                               )
    add_time = models.DateTimeField(auto_now_add=True,
                                    verbose_name="添加时间"
                                    )
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间"
                                       )
    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        db_table = "goods_img"
        verbose_name = "商品相册"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "商品相册"


# 首页轮播商品
class Cycle(models.Model):
    name = models.CharField(max_length=150,
                            verbose_name="名称"
                            )
    sku_id = models.ForeignKey(to=GoodsSku,
                               verbose_name="商品sku id"
                               )
    url = models.ImageField(verbose_name='轮播图片地址',
                            upload_to='banner/%Y%m/%d'
                            )
    order = models.SmallIntegerField(default=0,
                                     verbose_name="排序"
                                     )
    add_time = models.DateTimeField(auto_now_add=True,
                                    verbose_name="添加时间"
                                    )
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间"
                                       )
    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        db_table = "cycle"
        verbose_name = "轮播商品"
        verbose_name_plural = verbose_name


# 首页活动表
class Activity(models.Model):
    name = models.CharField(max_length=50,
                            verbose_name="活动名"
                            )
    img_url = models.ImageField(verbose_name='活动图片地址',
                                upload_to='activity/%Y%m/%d'
                                )
    url_site = models.URLField(verbose_name='活动的url地址', max_length=200)


    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        db_table = "activity"
        verbose_name = "首页活动表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 首页活动专区
class Special(models.Model):
    name = models.CharField(max_length=50,
                            verbose_name="活动专区名称"
                            )
    desc = models.CharField(max_length=100,
                            verbose_name="描述",
                            null=True,
                            blank=True,
                            )
    order = models.SmallIntegerField(default=0,
                                     verbose_name="排序"
                                     )
    is_on_sale = models.BooleanField(verbose_name="上否上线",
                                     choices=is_on_sale_choices,
                                     default=0,
                                     )
    add_time = models.DateTimeField(auto_now_add=True,
                                    verbose_name="添加时间"
                                    )
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间"
                                       )
    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        db_table = "special"
        verbose_name = "活动专区"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 首页专区活动商品表
class SpecialGoods(models.Model):
    special_id = models.ForeignKey(to="Special",
                                   verbose_name="活动专区id"
                                   )
    sku_id = models.ForeignKey(to="GoodsSku",
                               verbose_name="商品sku id"
                               )
    add_time = models.DateTimeField(auto_now_add=True,
                                    verbose_name="添加时间"
                                    )
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间"
                                       )
    isDelete = models.BooleanField(default=False,
                                   verbose_name="是否删除"
                                   )

    class Meta:
        db_table = "special_goods"
        verbose_name = "活动专区商品表"
        verbose_name_plural = verbose_name
