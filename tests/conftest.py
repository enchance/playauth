import pytest, asyncio, httpx
from decouple import config
from tortoise import Tortoise, connections

from main import get_app
from app import ic, red
from app.auth import Account
from app.db import DATABASE_URL, DATABASE_MODELS
from fixtures import init, SUPER_EMAIL, VERIFIED_EMAIL_SET, GROUP_FIXTURES_DEV, GROUP_FIXTURES_PROD


app = get_app()

@pytest.fixture(scope='session')
async def client(initdb):
    # async with TestClient(app) as tc:
    #     yield tc
    async with httpx.AsyncClient(app=app, base_url='http://test/') as ac:
        yield ac
        
        
@pytest.fixture(scope='session')
def event_loop():
    """
    DO NOT DELETE (even if not in use):
    Creates an instance of the default event loop for the test session.
    This overwrites the default scope of the event_loop from fn to session.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
    
    
@pytest.fixture(scope='session')
def seed():
    async def ab():
        await init()
    yield ab


@pytest.fixture(scope='session')
async def initdb(seed):
    # ic('INITIALIZING_DB')
    postgresurl = 'postgres://postgres:pass123@127.0.0.1:5432/postgres'
    dbname = 'playauth'
    
    stmt = '''
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{}' AND pid <> pg_backend_pid();
    '''.format(dbname)
    
    # Switch database so you can drop the other
    await Tortoise.init(db_url=postgresurl, modules={'models': DATABASE_MODELS})
    
    # Postgres
    conn = connections.get("default")
    await conn.execute_query(stmt)
    await conn.execute_query(f'DROP DATABASE {dbname}')             # noqa
    await conn.execute_query(f'CREATE DATABASE {dbname}')           # noqa
    
    # Redis
    red.flushdb()
    
    # Return to newly created database
    await Tortoise.init(db_url=DATABASE_URL, modules={'models': DATABASE_MODELS})
    await Tortoise.generate_schemas()
    
    # Seed
    await seed()


@pytest.fixture(scope='module')
async def account(initdb):
    account = await Account.get_or_none(email=list(VERIFIED_EMAIL_SET)[0]).prefetch_related('groups')
    return account


@pytest.fixture(scope='module')
async def superuser(initdb):
    account = await Account.get_or_none(email=SUPER_EMAIL).prefetch_related('groups')
    return account


@pytest.fixture(scope='module')
def group_fixture_data():
    data = config('ENV') == 'development' and GROUP_FIXTURES_DEV or GROUP_FIXTURES_PROD
    d = {
        'groups': list(data.keys())
    }

    for name, permdata in data.items():
        permset = set()
        for title, perms in permdata.items():
            for i in perms:
                permset.add(f'{title}.{i}')
        d[name] = permset
    return d
