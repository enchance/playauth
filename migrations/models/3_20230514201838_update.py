from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_group" ALTER COLUMN "description" SET DEFAULT '';
        ALTER TABLE "auth_role" ALTER COLUMN "description" SET DEFAULT '';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_role" ALTER COLUMN "description" DROP DEFAULT;
        ALTER TABLE "auth_group" ALTER COLUMN "description" DROP DEFAULT;"""
