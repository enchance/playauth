from tortoise import models
from tortoise.exceptions import OperationalError
from fastapi_users_tortoise import TortoiseUserDatabase, TortoiseBaseUserAccountModelUUID

from .dbmods import AccountMod, GroupMod


class Group(GroupMod, models.Model):
    class Meta:
        table = 'auth_group'
        ordering = ['name']
    
    @staticmethod
    def foo() -> str:
        return 'bar'
    
    
class Account(AccountMod, TortoiseBaseUserAccountModelUUID):
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
    
    def get_options(self) -> dict:
        return self.options
    
    def _collate_permissions(self) -> list[str]:
        # TODO: Get collated perms from cache
        return ['a', 'b', 'c', 'd']
    
    # TESTME: Untested
    # TODO: Allow group names instead of permissions
    def has(self, *args: str, partials: bool = True) -> bool:
        """
        Check if the account has the following permission.
        :param args:        List of permissions
        :param partials:    Allow matching part of the list instead of all.
        :return:            bool
        """
        datalist = self._collate_permissions()
        shared = set(args).intersection(set(datalist))
        if partials:
            return bool(shared)
        return len(shared) == len(args)
    
    # TESTME: Untested
    async def attach_group(self, group: Group) -> bool:
        try:
            if self.has('group.attach'):
                await self.groups.add(group)
            return True
        except OperationalError:
            return False
        
    # TESTME: Untested
    async def _has_group(self, name: str) -> bool:
        """Check if user is a part of the group."""
        # TODO: Check group
        return True