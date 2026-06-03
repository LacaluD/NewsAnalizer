import os

# Ensure settings module can be imported in tests without local .env.
os.environ.setdefault("AI_TOKEN", "test-ai-token")
os.environ.setdefault("TG_BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("OWNER_TG_ID", "1")
os.environ.setdefault("ADMIN_CHAT_ID", "2")
