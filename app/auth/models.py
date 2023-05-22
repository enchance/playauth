from __future__ import annotations
import uuid
from tortoise import models
from tortoise.exceptions import OperationalError
from fastapi_users_tortoise import TortoiseUserDatabase, TortoiseBaseUserAccountModelUUID
from fastapi.exceptions import HTTPException
from redis.exceptions import RedisError

from app import red, settings as s, ic, PermissionsException
from .dbmods import *


class Group(GroupMod, models.Model):
    class Meta:
        table = 'auth_group'
        ordering = ['name']
    
    # @staticmethod
    # def cache_user_groups(account):
    #     pass

    # # TESTME: Untested
    # @property
    # async def permissionset(self) -> set[str]:
    #     """Get permissions of a group."""
    #     cachekey = s.redis.GROUP_PERMISSIONS.format(self.name)
    #
    #     def _cachedata() -> set[str]:
    #         data = red.get(cachekey, set())
    #         return data
    #
    #     def _dbdata() -> set[str]:
    #         if data := self.permissions:
    #             red.set(cachekey, set(data))
    #             return set(data)
    #         return set()
    #
    #     dataset = _cachedata() or _dbdata()
    #     return dataset


class Role(RoleMod, models.Model):
    class Meta:
        table = 'auth_role'
        ordering = ['name']
        
    
class Account(AccountMod, TortoiseBaseUserAccountModelUUID):
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
    
    # TESTME: Untested
    def get_options(self) -> dict:
        return self.options
    
    
    @property
    async def custom_perms(self) -> set[str]:
        dataset = set()
        
        async def _dbdata() -> set[str]:
            # TODO: Get from db
            return set()
        
        return dataset
    
    
    @property
    async def groups(self) -> set[str]:
        """Get collated group names of user."""
        cachekey = s.redis.ACCOUNT_GROUPS.format(self.id)

        def _cachedata() -> set[str]:        # noqa
            data = red.get(cachekey) or set()
            return data

        async def _dbdata() -> set[str]:
            groups = set(self.role.groups) or set()
            red.set(cachekey, groups)
            return groups

        dataset = _cachedata() or await _dbdata()
        return dataset


    @property
    async def permissions(self) -> set[str]:
        """Get collated permissions of user from their groups."""

        async def _cachedata() -> set[str]:        # noqa
            set_ = set()
            for name in await self.groups:
                cachekey = s.redis.GROUP_PERMISSIONS.format(name)
                cached_data = red.get(cachekey, set())
                set_ = set_.union(cached_data)
            return set_

        async def _dbdata() -> set[str]:
            set_ = set()
            groupset = await self.groups
            groups = await Group.filter(name__in=groupset)
            for i in groups:
                cachekey = s.redis.GROUP_PERMISSIONS.format(i.name)
                red.set(cachekey, set(i.permissions))
                set_ = set_.union(set(i.permissions))      # noqa
            return set_

        dataset = await _cachedata() or await _dbdata()
        return dataset

    
    async def has(self, *args: str, partials: bool = True) -> bool:
        """
        Check if the account has the following permission/s and/or group/s.
        This is where any custom permissions are applied since only group perms are saved to cache
        and not account perms. This makes it easier to manage and with less redis keys.
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
        permset = set()
        groupset = set()
        
        def _custom_account_perms() -> set[str]:
            return self.perms or set()
        
        if not args:
            return False
        
        for i in args:
            if len(i.split('.')) > 1:
                permset.add(i)
            else:
                groupset.add(i)
        
        if permset:
            permdata = await self.permissions

            if custom_perms := _custom_account_perms():
                for i in custom_perms:
                    i = i.strip()
                    if i[0] == '-':
                        permdata = permdata - set(i[1:])
                    else:
                        permdata = permdata | set(i)
            
            shared = permset & permdata
            hits += len(shared)

        if groupset:
            groupdata = await self.groups
            shared = groupset & groupdata
            hits += len(shared)
            
        if partials:
            return hits > 0
        return hits == len(args)
    
    
    # TESTME: Untested
    async def change_role(self, account: Account, role: Role):
        """
        Change the role of an account. Cannot be used to make admin accounts.
        :param account:     Account to change
        :param role:        New role
        :return:            None
        :raises             PermissionException
        """
        if not self.has('role.update') or self.id == account.id:
            raise PermissionsException()
        
        if account.role == role or role.name == 'admin':
            return
        
        account.role = role
        await account.save(update_fields=['role_id'])
        