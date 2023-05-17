module default {
    type User {
        required property email -> str {
            constraint exclusive;
            constraint regexp(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$");
        }

        required property hashed_password -> str;

        required property is_active -> bool {
            default := true;
        }
        required property is_superuser -> bool{
            default := false;
        }
        required property is_verified -> bool {
            default := false;
        }

        required property first_name -> str;
        required property last_name -> str;
        required property username -> str {
            constraint exclusive;
        }
        required property age -> Age;
    }

    abstract type Post {
        required property content -> str;
        property upvote -> int16{default := 0; }
        property downvote -> int16{default := 0; }
        required link author -> User;
    }

    type Question extending Post {
        required property title -> str;
        property tags -> array<str>;
        multi link comments -> Comment {
            on target delete allow;
        }
        multi link answer -> Answer {
            on target delete allow;
        }
    }

    type Answer extending Post {
        multi link comments -> Comment;
        property is_accepted -> bool{default := false};
    }

    type Comment extending Post {

    }

    scalar type Age extending int16{
        constraint max_value(110);
        constraint min_value(0);
    }
}