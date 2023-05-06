from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "auth_token";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ;"""
