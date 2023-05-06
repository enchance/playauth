from tortoise import models
from fastapi_users_tortoise import TortoiseUserDatabase, TortoiseBaseUserAccountModelUUID

from .dbmods import AccountMod, GroupMod


class Account(AccountMod, TortoiseBaseUserAccountModelUUID):
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
        
    def get_options(self) -> dict:
        return self.options
    
    
class Group(GroupMod):
    class Meta:
        table = 'auth_group'
        ordering = ['name']
        
    def foo(self) -> str:
        return 'bar'