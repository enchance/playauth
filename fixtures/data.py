

read_only = ['read']
crud = ['create', 'read', 'update', 'delete']
ru = ['read', 'update']
create = ['create', 'read', 'update']
attach = ['attach', 'detach']
hard_delete = ['hard-delete']



GROUP_FIXTURES = {
    'AdminGroup': {
        'description': 'Not sure what you are yet',
        'group': attach,
    },
    'AccountGroup': {
        'description': 'Account management',
        'account': ru,
    },
    'DemoGroup': {
        'description': 'Descriptive data',
        'demo': ['foo', 'bar']
    },
    'EmptyGroup': {
        'description': 'Nothing here'
    },
}