from tortoise import fields
from limeutils import modstr
from fastapi_users_tortoise import TortoiseBaseUserAccountModelUUID


class DTMixin(object):
    updated_on = fields.DatetimeField(auto_now=True)
    created_on = fields.DatetimeField(auto_now_add=True)
    deleted_on = fields.DatetimeField(null=True, index=True)


class Account(DTMixin, TortoiseBaseUserAccountModelUUID):
    username = fields.CharField(max_length=199, unique=True)
    email = fields.CharField(max_length=199, unique=True)
    
    class Meta:
        table = 'auth_account'
        ordering = ['username']
    
    def __repr__(self):
        return self.username

    