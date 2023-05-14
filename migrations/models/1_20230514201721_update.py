from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "auth_xaccountgroups";
        ALTER TABLE "auth_role" RENAME COLUMN "permissions" TO "groups";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_role" RENAME COLUMN "groups" TO "permissions";
        CREATE TABLE "auth_xaccountgroups" (
    "group_id" INT NOT NULL REFERENCES "auth_group" ("id") ON DELETE CASCADE,
    "account_id" UUID NOT NULL REFERENCES "auth_account" ("id") ON DELETE CASCADE
);"""
