from tinydb import TinyDB, Query


class Database:
    def __init__(self):
        self.db = TinyDB("database.json")
        self.users = self.db.table("users")

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
