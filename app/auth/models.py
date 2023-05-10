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
    
    # @staticmethod
    # def cache_user_groups(account):
    #     pass

    # TESTME: Untested
    @property
    async def permissionset(self) -> set[str]:
        """Get permissions of a group."""
        cachekey = s.redis.GROUP_PERMISSIONS.format(self.name)

        def _cachedata() -> set[str]:
            data = red.get(cachekey, set())
            return data

        def _dbdata() -> set[str]:
            if data := self.permissions:
                return set(data)
            return set()

        if dataset := _cachedata():
            pass
        elif dataset := _dbdata():
            red.set(cachekey, dataset)
        else:
            red.set(cachekey, dataset)
        return dataset
    
    
class Account(AccountMod, TortoiseBaseUserAccountModelUUID):
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
    
    # TESTME: Untested
    def get_options(self) -> dict:
        return self.options
    
    
    # TESTME: Untested
    @property
    async def groupset(self) -> set[str]:
        """Get collated group names of user."""
        cachekey = s.redis.ACCOUNT_GROUPS.format(self.id)

        def _cachedata() -> set[str]:        # noqa
            data = red.get(cachekey) or set()
            return data

        async def _dbdata() -> set[str]:
            groups = await Group.filter(groupaccounts__id=self.id).only('id', 'name')
            return {i.name for i in groups}

        if dataset := _cachedata():
            pass
        elif dataset := await _dbdata():
            red.set(cachekey, dataset)
        else:
            red.set(cachekey, dataset)
        return dataset


    # TESTME: Untested
    @property
    async def permissionset(self) -> set[str]:
        """Get collated permissions of user."""
        cachekey = s.redis.ACCOUNT_PERMISSIONS.format(self.id)

        def _cachedata() -> set[str]:        # noqa
            data = red.get(cachekey, set())
            return data

        async def _dbdata() -> set[str]:
            set_ = set()
            groupset = await self.groupset
            groups = await Group.filter(name__in=groupset)
            for i in groups:
                set_ = set_.union(await i.permissionset)      # noqa
            return set_

        if dataset := _cachedata():
            pass
        elif dataset := await _dbdata():
            red.set(cachekey, dataset)
        else:
            red.set(cachekey, dataset)
        return dataset

    
    # TESTME: Untested
    async def has(self, *args: str, partials: bool = True) -> bool:
        """
        Check if the account has the following permission/s and/or group/s.
        Example:
            account.has('foo.bar')
            account.has('FooGroup')
            
            # At least one much match
            account.has('foo.bar', 'FooGroup')
            
            # All must match
            account.has('foo.bar', 'FooGroup', partials=False)
        
        :param args:        List of permissions and/or groups
        :param partials:    Require all to match or just a subset
        :return:            bool
        """
        hits = 0
        
        if not args:
            return False
        
        permset = set()
        groupset = set()
        for i in args:
            if len(i.split('.')) > 1:
                permset.add(i)
            else:
                groupset.add(i)
        
        if permset:
            permdata = await self.permissionset
            shared = permset.intersection(permdata)
            hits += len(shared)

        if groupset:
            groupdata = await self.groupset
            shared = groupset.intersection(groupdata)
            hits += len(shared)
            
        if partials:
            return hits > 0
        return hits == len(args)
    
    
    # # TESTME: Untested
    # async def attach_group(self, group: Group) -> bool:
    #     try:
    #         if self.has('group.attach'):
    #             await self.groups.add(group)
    #         return True
    #     except OperationalError:
    #         return False
        