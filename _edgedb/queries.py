GET_ANSWER = """
    SELECT Answer {
        content,
        upvote,
        downvote,
        author,
        comments,
        is_accepted
    } FILTER .id = <uuid>$id
"""
