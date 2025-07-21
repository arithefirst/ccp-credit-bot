from tinydb import TinyDB, Query


class Database:
    def __init__(self):
        self.db = TinyDB("database.json")
        self.users = self.db.table("users")
        self.cache = self.db.table("cache")

    def update_social_credit(self, user_id, server_id, amount):
        User = Query()
        existing_user = self.users.search(
            (User.id == user_id) & (User.server_id == server_id)
        )

        if existing_user:
            # User exists, update their credit amount
            current_credit = existing_user[0].get("credit_amount", 0)
            new_credit = current_credit + amount
            self.users.update(
                {"credit_amount": new_credit},
                (User.id == user_id) & (User.server_id == server_id),
            )
        else:
            # User doesn't exist, create new user with the amount
            self.users.insert(
                {"id": user_id, "server_id": server_id, "credit_amount": amount}
            )

    def get_social_credit_server(self, server_id):
        User = Query()
        return self.users.search(User.server_id == server_id)

    def cache_message_value(self, message_content, score):
        Cache = Query()

        # Hash the message content to use as a key
        import hashlib

        message_hash = hashlib.md5(message_content.encode()).hexdigest()

        existing_cache = self.cache.get(Cache.message_hash == message_hash)

        if existing_cache:
            # Update existing cache entry
            self.cache.update(
                {"score": score, "timestamp": self._get_timestamp()},
                Cache.message_hash == message_hash,
            )
        else:
            # Create new cache entry
            self.cache.insert(
                {
                    "message_hash": message_hash,
                    "score": score,
                    "timestamp": self._get_timestamp(),
                }
            )

    def get_cached_score(self, message_content):
        Cache = Query()

        # Hash the message content to use as a key
        import hashlib

        message_hash = hashlib.md5(message_content.encode()).hexdigest()

        result = self.cache.get(Cache.message_hash == message_hash)

        if result:
            # Check if cache is still valid (optional: implement expiry)
            return result.get("score")
        return None

    def _get_timestamp(self):
        # Get current timestamp for cache entries
        from datetime import datetime

        return datetime.now().timestamp()

    def clear_old_cache(self, max_age_days=7):
        from datetime import datetime, timedelta

        Cache = Query()

        cutoff_time = (datetime.now() - timedelta(days=max_age_days)).timestamp()
        self.cache.remove(Cache.timestamp < cutoff_time)
