

read_only = ['read']
crud = ['create', 'read', 'update', 'delete']
ru = ['read', 'update']
create = ['create', 'read', 'update']
attach = ['attach', 'detach']
hard_delete = ['hard-delete']



GROUP_FIXTURES_DEV = {
    'AdminGroup': {
        'description': 'Not sure what you are yet',
        'group': attach,
    },
    'AccountGroup': {
        'description': 'Account management',
        'account': ru,
    },
    'EmptyGroup': {
        'description': 'Nothing here',
    },
}

GROUP_FIXTURES_PROD = {}