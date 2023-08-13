-- old `chat`, `page`, `book` tables here

-- new `role` and `user_role` tables here

-- create scheduler to track expiration of user roles
CREATE EVENT role_expiration
    ON SCHEDULE
        EVERY 1 DAY
    COMMENT 'Check expiration date of user role every day'
    DO
        DELETE FROM user_role WHERE CURDATE() > user_role.expiration;
