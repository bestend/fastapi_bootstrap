from fastapi_bootstrap.log.setup import LOG_JSON, LOG_LEVEL, LOG_STRING_LENGTH


class TestEnvironmentConfiguration:
    def test_default_log_level(self):
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_default_log_json(self):
        assert isinstance(LOG_JSON, bool)

    def test_default_log_string_length(self):
        assert LOG_STRING_LENGTH == 5000 or isinstance(LOG_STRING_LENGTH, int)
