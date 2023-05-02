from uuid import UUID
from tortoise import fields
from limeutils import modstr
from fastapi_users_tortoise import TortoiseBaseUserAccountModelUUID, TortoiseUserDatabase


class DTMixin(object):
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    deleted_at = fields.DatetimeField(null=True, index=True)


class Account(DTMixin, TortoiseBaseUserAccountModelUUID):
    display = fields.CharField(max_length=199)
    
    # # OAuth
    # oauth_id: str = fields.CharField(null=True, max_length=255)
    # oauth_name: str = fields.CharField(null=True, max_length=100)
    # access_token: str = fields.CharField(null=True, max_length=1024)
    # refresh_token: str = fields.CharField(null=True, max_length=1024)
    # expires_at: int = fields.IntField(null=True)
    
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
    
    def __repr__(self):
        return self.display


async def get_user_db():
    yield TortoiseUserDatabase(Account)