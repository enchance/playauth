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
    "display" VARCHAR(199) NOT NULL,
    "is_banned" BOOL NOT NULL  DEFAULT False,
    "options" JSONB NOT NULL,
    "permissions" text[],
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(1024) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_superuser" BOOL NOT NULL  DEFAULT False,
    "is_verified" BOOL NOT NULL  DEFAULT False,
    "id" UUID NOT NULL  PRIMARY KEY
);
CREATE INDEX IF NOT EXISTS "idx_auth_accoun_deleted_112596" ON "auth_account" ("deleted_at");
CREATE INDEX IF NOT EXISTS "idx_auth_accoun_email_3074e7" ON "auth_account" ("email");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
