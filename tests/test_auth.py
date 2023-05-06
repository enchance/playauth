import pytest
from pytest import mark

from app import ic



class TestAuth:
    # @mark.focus
    async def test_accounts(self, initdb):
        assert True