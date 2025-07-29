from unittest.mock import patch

from app.utils import redis_client as rc


@patch("app.utils.redis_client.redis_client")
async def test_set_token_sets_token_and_email(mock_redis):
    mock_redis.get.return_value = None

    await rc.set_token("user@example.com", "token123", ttl_seconds=900)

    mock_redis.get.assert_awaited_once_with("reset:email:user@example.com")
    mock_redis.set.assert_any_await("reset:token123", "user@example.com", ex=900)
    mock_redis.set.assert_any_await("reset:email:user@example.com", "token123", ex=900)


@patch("app.utils.redis_client.redis_client")
async def test_set_token_deletes_old_token_if_exists(mock_redis):
    mock_redis.get.return_value = "old_token"

    await rc.set_token("user@example.com", "new_token", ttl_seconds=900)

    mock_redis.delete.assert_awaited_once_with("reset:old_token")
    mock_redis.set.assert_any_await("reset:new_token", "user@example.com", ex=900)
    mock_redis.set.assert_any_await("reset:email:user@example.com", "new_token", ex=900)


@patch("app.utils.redis_client.redis_client")
async def test_get_email_by_token(mock_redis):
    mock_redis.get.return_value = "user@example.com"

    result = await rc.get_email_by_token("token123")

    mock_redis.get.assert_awaited_once_with("reset:token123")
    assert result == "user@example.com"


@patch("app.utils.redis_client.redis_client")
async def test_delete_token_existing_email(mock_redis):
    mock_redis.get.return_value = "user@example.com"

    await rc.delete_token("token123")

    mock_redis.get.assert_awaited_once_with("reset:token123")
    mock_redis.delete.assert_any_await("reset:email:user@example.com")
    mock_redis.delete.assert_any_await("reset:token123")


@patch("app.utils.redis_client.redis_client")
async def test_delete_token_without_email(mock_redis):
    mock_redis.get.return_value = None

    await rc.delete_token("token123")

    mock_redis.delete.assert_awaited_once_with("reset:token123")


@patch("app.utils.redis_client.redis_client")
async def test_is_reset_request_allowed_true(mock_redis):
    mock_redis.exists.return_value = False

    allowed = await rc.is_reset_request_allowed("user@example.com")

    mock_redis.set.assert_awaited_once_with("reset_limit:user@example.com", "1", ex=60)
    assert allowed is True


@patch("app.utils.redis_client.redis_client")
async def test_is_reset_request_allowed_false(mock_redis):
    mock_redis.exists.return_value = True

    allowed = await rc.is_reset_request_allowed("user@example.com")

    mock_redis.set.assert_not_called()
    assert allowed is False


@patch("app.utils.redis_client.redis_client")
async def test_store_refresh_token(mock_redis):
    await rc.store_refresh_token(42, "refresh_token_abc", ttl_seconds=604800)
    mock_redis.set.assert_awaited_once_with(
        "refresh:42", "refresh_token_abc", ex=604800
    )


@patch("app.utils.redis_client.redis_client")
async def test_get_refresh_token(mock_redis):
    mock_redis.get.return_value = "refresh_token_abc"

    result = await rc.get_refresh_token(42)

    mock_redis.get.assert_awaited_once_with("refresh:42")
    assert result == "refresh_token_abc"


@patch("app.utils.redis_client.redis_client")
async def test_delete_refresh_token(mock_redis):
    await rc.delete_refresh_token(42)

    mock_redis.delete.assert_awaited_once_with("refresh:42")
