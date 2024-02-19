'''Custom django admin panel'''

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BasUserAdmin

from core import models


class UserAdmin(BasUserAdmin):
    '''defining custum admin panel'''
    ordering = ['id']
    list_display = ['name', 'email']


admin.site.register(models.User, UserAdmin)
