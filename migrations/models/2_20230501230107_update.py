from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_account" RENAME COLUMN "deleted_on" TO "deleted_at";
        ALTER TABLE "auth_account" RENAME COLUMN "created_on" TO "created_at";
        ALTER TABLE "auth_account" RENAME COLUMN "updated_on" TO "updated_at";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_account" RENAME COLUMN "updated_at" TO "updated_on";
        ALTER TABLE "auth_account" RENAME COLUMN "created_at" TO "created_on";
        ALTER TABLE "auth_account" RENAME COLUMN "deleted_at" TO "deleted_on";"""
