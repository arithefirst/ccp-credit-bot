from tinydb import TinyDB, Query
import pytz


class Database:
    def __init__(self):
        self.db = TinyDB("database.json")
        self.users = self.db.table("users")
        self.cache = self.db.table("cache")

    ## Social Credit Stuff

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

    ## Timezone stuff
    def update_timezone(self, user_id, server_id, timezone):

        # Validate timezone using pytz
        if timezone not in pytz.all_timezones:
            raise ValueError(f"Invalid IANA timezone: {timezone}")

        User = Query()
        existing_user = self.users.search(
            (User.id == user_id) & (User.server_id == server_id)
        )

        if existing_user:
            self.users.update(
                {"timezone": timezone},
                (User.id == user_id) & (User.server_id == server_id),
            )
        else:
            self.users.insert(
                {"id": user_id, "server_id": server_id, "timezone": timezone}
            )

    ## Caching stuff

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

    def get_cached_score(self, message_content, max_age_hours=24):
        Cache = Query()

        # Hash the message content to use as a key
        import hashlib

        message_hash = hashlib.md5(message_content.encode()).hexdigest()

        result = self.cache.get(Cache.message_hash == message_hash)

        if result:
            # Check if cache is still valid
            from datetime import datetime

            cache_timestamp = result.get("timestamp")
            current_timestamp = datetime.now().timestamp()
            age_hours = (current_timestamp - cache_timestamp) / 3600

            if age_hours <= max_age_hours:
                return result.get("score")
            else:
                # Cache entry is expired, remove it
                self.cache.remove(Cache.message_hash == message_hash)
                return None
        return None

    def _get_timestamp(self):
        # Get current timestamp for cache entries
        from datetime import datetime

        return datetime.now().timestamp()

    def clear_old_cache(self, max_age_hours=24):
        from datetime import datetime

        Cache = Query()

        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        removed_count = len(self.cache.search(Cache.timestamp < cutoff_time))
        self.cache.remove(Cache.timestamp < cutoff_time)
        return removed_count
