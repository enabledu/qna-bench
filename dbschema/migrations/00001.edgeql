CREATE MIGRATION m1nb2vtbmjqeigxkgcheyly6z7bi2ik7a5iucfscbjmzczug6uzurq
    ONTO initial
{
  CREATE SCALAR TYPE default::Age EXTENDING std::int16 {
      CREATE CONSTRAINT std::max_value(110);
      CREATE CONSTRAINT std::min_value(0);
  };
  CREATE TYPE default::User {
      CREATE REQUIRED PROPERTY age -> default::Age;
      CREATE REQUIRED PROPERTY email -> std::str {
          CREATE CONSTRAINT std::exclusive;
          CREATE CONSTRAINT std::regexp(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$');
      };
      CREATE REQUIRED PROPERTY first_name -> std::str;
      CREATE REQUIRED PROPERTY hashed_password -> std::str;
      CREATE REQUIRED PROPERTY is_active -> std::bool {
          SET default := true;
      };
      CREATE REQUIRED PROPERTY is_superuser -> std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY is_verified -> std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY last_name -> std::str;
      CREATE REQUIRED PROPERTY username -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE ABSTRACT TYPE default::Post {
      CREATE REQUIRED LINK author -> default::User;
      CREATE REQUIRED PROPERTY content -> std::str;
      CREATE PROPERTY downvote -> std::int16 {
          SET default := 0;
      };
      CREATE PROPERTY upvote -> std::int16 {
          SET default := 0;
      };
  };
  CREATE TYPE default::Comment EXTENDING default::Post;
  CREATE TYPE default::Answer EXTENDING default::Post {
      CREATE MULTI LINK comments -> default::Comment;
      CREATE PROPERTY is_accepted -> std::bool {
          SET default := false;
      };
  };
  CREATE TYPE default::Question EXTENDING default::Post {
      CREATE MULTI LINK answers -> default::Answer {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK comments -> default::Comment {
          ON TARGET DELETE ALLOW;
      };
      CREATE PROPERTY tags -> array<std::str>;
      CREATE REQUIRED PROPERTY title -> std::str;
  };
};
