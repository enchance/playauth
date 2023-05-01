from uuid import UUID
from tortoise import fields
from limeutils import modstr
from fastapi_users_tortoise import TortoiseBaseUserAccountModelUUID, TortoiseBaseUserOAuthAccountModelUUID


class DTMixin(object):
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    deleted_at = fields.DatetimeField(null=True, index=True)


class Account(DTMixin, TortoiseBaseUserAccountModelUUID):
    # account_email = None
    # user = None
    #
    display = fields.CharField(max_length=199)
    email: str = fields.CharField(max_length=255, unique=True)
    # hashed_password = fields.CharField(max_length=199)
    # is_active = fields.BooleanField(default=True, null=False)
    # is_superuser = fields.BooleanField(default=False, null=False)
    # is_verified = fields.BooleanField(default=False, null=False)
    
    # OAuth
    oauth_id: str = fields.CharField(null=True, max_length=255)
    oauth_name: str = fields.CharField(null=True, max_length=100)
    access_token: str = fields.CharField(null=True, max_length=1024)
    refresh_token: str = fields.CharField(null=True, max_length=1024)
    expires_at: int = fields.IntField(null=True)
    
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
    
    def __repr__(self):
        return self.display
