# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-20 15:32
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SpUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=11, validators=[django.core.validators.RegexValidator('^1[3-9]\\d{9}$', '手机号码格式错误!')], verbose_name='手机号码')),
                ('nickname', models.CharField(blank=True, max_length=50, null=True, verbose_name='昵称')),
                ('password', models.CharField(max_length=32, verbose_name='密码')),
                ('gender', models.SmallIntegerField(choices=[(1, '男'), (2, '女')], default=1, verbose_name='性别')),
                ('school_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='学校')),
                ('hometown', models.CharField(blank=True, max_length=50, null=True, verbose_name='家乡')),
                ('birth_of_date', models.DateField(blank=True, null=True, verbose_name='出生日期')),
                ('address', models.CharField(blank=True, max_length=255, null=True, verbose_name='详细位置')),
                ('add_time', models.DateTimeField(auto_now_add=True, verbose_name='添加时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('isDelete', models.BooleanField(default=False, verbose_name='是否删除')),
            ],
            options={
                'verbose_name': '用户管理',
                'verbose_name_plural': '用户管理',
                'db_table': 'sp_user',
            },
        ),
    ]