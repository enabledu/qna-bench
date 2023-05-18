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

GET_COMMENTS_ON_QUESTION = """
    WITH comments_ids := (SELECT Question FILTER .id = <uuid>$id).comments.id
    SELECT Comment{
    content,
    upvote,
    downvote,
    author
    } FILTER .id IN comments_ids
"""

INSERT_USER = """
    SELECT (
        INSERT User {
            age := <Age>$age,
            email := <str>$email,
            first_name := <str>$fname,
            last_name := <str>$lname,
            username := <str>$username,
            hashed_password := <str>$hashed_password,
        }
    ) {
        id,
        username,
        email,
        age,
        first_name, 
        last_name,
    }
"""

UPDATE_COMMENTS_ON_ANSWER = """
    SELECT (
        UPDATE Answer FILTER .id = <uuid>$answer_id
        SET {
            comments += (
                INSERT Comment {
                    upvote := <int16>$upvote,
                    downvote := <int16>$downvote,
                    content := <str>$content,
                    author := (SELECT User FILTER .id = <uuid>$author_id)
                }
            )
        }
    ) {
        id,
        comments,
    }
"""