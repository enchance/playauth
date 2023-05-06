from uuid import UUID
from datetime import datetime
from tortoise import fields as f, models
from tortoise.contrib.postgres.fields import ArrayField
from limeutils import modstr
from fastapi_users_tortoise import TortoiseBaseUserAccountModelUUID, TortoiseUserDatabase

from app.settings import settings as s



HASH_FIELD = f.CharField(max_length=70)
HASH_FIELD_INDEXED = f.CharField(max_length=70, unique=True)


class DTMixin:
    updated_at = f.DatetimeField(auto_now=True)
    created_at = f.DatetimeField(auto_now_add=True)
    deleted_at = f.DatetimeField(null=True, index=True)


class AccountMod(DTMixin):
    display = f.CharField(max_length=199)
    is_banned = f.BooleanField(default=False)
    options = f.JSONField(default=s.ACCOUNT_OPTIONS)
    permissions = ArrayField('text', null=True)

    # groups = f.ManyToManyField('models.Group', related_name='groupaccounts',
    #                            through='auth_xaccountgroups',
    #                            backward_key='account_id', forward_key='group_id')
    
    # # OAuth
    # oauth_id: str = f.CharField(null=True, max_length=255)
    # oauth_name: str = f.CharField(null=True, max_length=100)
    # access_token: str = f.CharField(null=True, max_length=1024)
    # refresh_token: str = f.CharField(null=True, max_length=1024)
    # expires_at: int = f.IntField(null=True)
    
    def __repr__(self):
        return modstr(self, 'display', 'email')
    
    
# class GroupMod(models.Model):
#     name = f.CharField(max_length=20, unique=True)
#     description = f.CharField(max_length=199)
#     permissions = ArrayField('text', null=True)
#
#     class Meta:
#         table = 'auth_group'
#         ordering = ['name']
#
#     def __repr__(self):
#         return modstr(self, 'name')