from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "auth_account" (
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(1024) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_superuser" BOOL NOT NULL  DEFAULT False,
    "is_verified" BOOL NOT NULL  DEFAULT False,
    "id" UUID NOT NULL  PRIMARY KEY,
    "display" VARCHAR(199) NOT NULL,
    "is_banned" BOOL NOT NULL  DEFAULT False
);
CREATE INDEX IF NOT EXISTS "idx_auth_accoun_deleted_112596" ON "auth_account" ("deleted_at");
CREATE INDEX IF NOT EXISTS "idx_auth_accoun_email_3074e7" ON "auth_account" ("email");
CREATE TABLE IF NOT EXISTS "auth_group" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(20) NOT NULL UNIQUE,
    "description" VARCHAR(199) NOT NULL,
    "permissions" text[]
);
CREATE TABLE IF NOT EXISTS "auth_xaccountgroups" (
    "account_id" UUID NOT NULL REFERENCES "auth_account" ("id") ON DELETE CASCADE,
    "group_id" INT NOT NULL REFERENCES "auth_group" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
