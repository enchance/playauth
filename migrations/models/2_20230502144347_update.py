from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_account" DROP COLUMN "expires_at";
        ALTER TABLE "auth_account" DROP COLUMN "oauth_id";
        ALTER TABLE "auth_account" DROP COLUMN "oauth_name";
        ALTER TABLE "auth_account" DROP COLUMN "refresh_token";
        ALTER TABLE "auth_account" DROP COLUMN "access_token";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_account" ADD "expires_at" INT;
        ALTER TABLE "auth_account" ADD "oauth_id" VARCHAR(255);
        ALTER TABLE "auth_account" ADD "oauth_name" VARCHAR(100);
        ALTER TABLE "auth_account" ADD "refresh_token" VARCHAR(1024);
        ALTER TABLE "auth_account" ADD "access_token" VARCHAR(1024);"""
