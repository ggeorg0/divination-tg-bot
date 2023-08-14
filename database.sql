-- old `chat`, `page`, `book` tables here

-- new `role` and `chat_role` tables here

-- create scheduler to track expiration of user roles
CREATE EVENT role_expiration
    ON SCHEDULE
        EVERY 1 DAY
        -- event starts tomorrow at 3 am
        STARTS CURDATE() + INTERVAL 1 DAY + INTERVAL 3 HOUR
    COMMENT 'Check expiration date of user role every day'
    DO
        DELETE FROM chat_role WHERE CURDATE() > chat_role.expiration;
