import random

MAX_POINTS_PER = 50
MIN_POINTS_PER = -50


def process_message(message, db):
    words = message.lower().split(" ")

    score = 0

    for word in words:

        if word.lower() == "femboy":
            word_score = 15
        if word.lower() == "america":
            word_score = -15
        else:
            cached_score = db.get_cached_score(word)
            if cached_score is not None:
                # Use cached score
                word_score = cached_score
            else:
                # Generate new score and cache it
                word_score = random.randint(-10, 10)
                db.cache_message_value(word, word_score)

        score += word_score

    return max(min(score, MAX_POINTS_PER), MIN_POINTS_PER)
