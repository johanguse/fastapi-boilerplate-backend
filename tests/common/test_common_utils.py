import pytest

from src.common import utils as common_utils
from src.common.exceptions import APIError


@pytest.mark.asyncio
async def test_handle_errors_success():
    async def ok(x):
        return x * 2

    result = await common_utils.handle_errors(ok, 3)
    assert result == 6


@pytest.mark.asyncio
async def test_handle_errors_apierror_passthrough():
    async def bad():
        raise APIError(status_code=404, detail='missing')

    with pytest.raises(APIError) as exc:
        await common_utils.handle_errors(bad)
    assert exc.value.status_code == 404
    assert 'missing' in exc.value.detail


@pytest.mark.asyncio
async def test_handle_errors_wraps_unexpected(monkeypatch):
    async def boom():
        raise ValueError('boom')

    logs = {'called': False}

    class DummyLogger:
        def exception(self, *_args, **_kwargs):
            logs['called'] = True

    monkeypatch.setattr(common_utils, 'logger', DummyLogger())

    with pytest.raises(APIError) as exc:
        await common_utils.handle_errors(boom)
    assert exc.value.status_code == 500
    assert logs['called'] is True
