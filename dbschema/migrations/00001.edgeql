CREATE MIGRATION m1babyutae6pje76rmpnxhidd5dclv7vd7356ru56lrxs3l3emrwxq
    ONTO initial
{
  CREATE TYPE default::Post {
      CREATE REQUIRED PROPERTY content -> std::str;
      CREATE PROPERTY downvote -> std::int16 {
          SET default := 0;
      };
      CREATE PROPERTY upvote -> std::int16 {
          SET default := 0;
      };
  };
};
