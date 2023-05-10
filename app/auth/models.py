import uuid
from tortoise import models
from tortoise.exceptions import OperationalError
from fastapi_users_tortoise import TortoiseUserDatabase, TortoiseBaseUserAccountModelUUID
from redis.exceptions import RedisError

from app import red, settings as s
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
    
    # TESTME: Untested
    def get_options(self) -> dict:
        return self.options
    
    def _collate_permissions_from_cache(self) -> set[str]:
        try:
            cachekey = s.redis.ACCOUNT_PERMISSIONS.format(self.id)
            dataset = red.get(cachekey) or set()
            return dataset
        except RedisError:
            return set()
    
    # TESTME: Untested
    # TODO: Allow group names instead of permissions
    def has(self, *args: str, partials: bool = True) -> bool:
        """
        Check if the account has the following permission.
        :param args:        List of permissions
        :param partials:    Allow matching part of the list instead of all.
        :return:            bool
        """
        if not args:
            return False
        
        if _ := len(args[0].split('.')) == 2:
            # Permissions
            dataset = self._collate_permissions_from_cache()
        else:
            # Groups
            cachekey = s.redis.ACCOUNT_GROUPS.format(self.id)
            dataset = red.get(cachekey) or set()
        
        shared = set(args).intersection(dataset)
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