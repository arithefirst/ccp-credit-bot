from jsondb import JsonDB


class Database:
    def __init__(self):
        self.db = JsonDB("database.json")
        self.db.create_table("users")

    def update_social_credit(self, user_id, server_id, amount):
        # Check if user exists
        existing_user = self.db.get_data(
            "users", {"id": user_id, "server_id": server_id}
        )

        if existing_user:
            # User exists, update their credit amount
            current_credit = existing_user[0].get("credit_amount", 0)
            new_credit = current_credit + amount
            self.db.update_data(
                "users",
                {"id": user_id, "server_id": server_id},
                {"credit_amount": new_credit},
            )
        else:
            # User doesn't exist, create new user with the amount
            self.db.insert_data(
                "users",
                {"id": user_id, "server_id": server_id, "credit_amount": amount},
            )

    def get_social_credit_server(self, server_id):
        data = self.db.get_data("users", {"server_id": server_id})
        return data
