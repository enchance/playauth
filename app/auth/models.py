from fastapi_users_tortoise import TortoiseUserDatabase, TortoiseBaseUserAccountModelUUID

from .dbmod import AccountMod


class Account(AccountMod, TortoiseBaseUserAccountModelUUID):
    class Meta:
        table = 'auth_account'
        ordering = ['display', 'email']
        
    def get_options(self) -> dict:
        return self.permissions


async def get_user_db():
    yield TortoiseUserDatabase(Account)