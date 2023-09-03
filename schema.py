import logging
import sys

WARN_MSG = """built-in dict class has the ability to remember insertion order in Python 3.7 or above, 
your Python version is %s.%s.%s. It means the table creation order may be incorrect."""

CREATE_STATEMENTS = {}
INSERT_STATEMENTS = {}

CREATE_STATEMENTS['schema'] = """
CREATE SCHEMA `test_bot_db` DEFAULT CHARACTER SET utf8 ;
"""

CREATE_STATEMENTS['use schema'] = """
USE `test_bot_db`;
"""

CREATE_STATEMENTS['table book'] = """
CREATE TABLE IF NOT EXISTS `book` (
    `id` SMALLINT UNSIGNED NOT NULL,
    `title` VARCHAR(1024) NULL,
    `author` VARCHAR(1024) NULL,
    `info` VARCHAR(2048) NULL,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB;
"""

CREATE_STATEMENTS['table chat'] = """
CREATE TABLE IF NOT EXISTS `chat` (
    `id` BIGINT UNSIGNED NOT NULL,
    `book_id` SMALLINT UNSIGNED NULL,
    `hex_color` CHAR(6) NULL,
    PRIMARY KEY (`id`),
    INDEX `fk_chat_book_id_idx` (`book_id` ASC) VISIBLE,
    CONSTRAINT `fk_chat_book_id`
        FOREIGN KEY (`book_id`)
        REFERENCES `book` (`id`)
) ENGINE = InnoDB;
"""

CREATE_STATEMENTS['table page'] = """
CREATE TABLE IF NOT EXISTS `page` (
    `book_id` SMALLINT UNSIGNED NOT NULL,
    `num` MEDIUMINT NOT NULL,
    `content` VARCHAR(4096) NULL,
    PRIMARY KEY (`book_id`, `num`),
    CONSTRAINT `fk_page_book_id`
        FOREIGN KEY (`book_id`)
        REFERENCES `book` (`id`)
) ENGINE = InnoDB;
"""


CREATE_STATEMENTS['table role'] = """
CREATE TABLE IF NOT EXISTS `role` (
    `id` INT UNSIGNED NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `info` VARCHAR(1024) NULL,
    PRIMARY KEY (`id`),
    UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE
) ENGINE = InnoDB;
"""


CREATE_STATEMENTS['table chat_role'] = """
CREATE TABLE IF NOT EXISTS `chat_role` (
    `chat_id` BIGINT UNSIGNED NOT NULL,
    `role_id` INT UNSIGNED NOT NULL,
    `grant_date` DATE NOT NULL,
    `expire_date` DATE NULL,
    PRIMARY KEY (`chat_id`, `role_id`),
    INDEX `fk_chat_role_role_id_idx` (`role_id` ASC) INVISIBLE,
    CONSTRAINT `fk_chat_role_chat_id`
        FOREIGN KEY (`chat_id`)
        REFERENCES `chat` (`id`),
    CONSTRAINT `fk_chat_role_role_id`
        FOREIGN KEY (`role_id`)
        REFERENCES `role` (`id`)
) ENGINE = InnoDB;
"""

CREATE_STATEMENTS['trigger chat_role_BEFORE_INSERT'] = """
CREATE TRIGGER `chat_role_BEFORE_INSERT` BEFORE INSERT ON `chat_role`
FOR EACH ROW
BEGIN
	IF NEW.grant_date <= CURDATE() THEN
		SET NEW.grant_date = CURDATE();
	END IF;
END
"""

CREATE_STATEMENTS['view chat_role_view'] = """
CREATE OR REPLACE VIEW chat_role_view AS
    SELECT chat_id, role.name as role_name, expire_date
		FROM chat_role INNER JOIN role 
			ON chat_role.role_id = role.id
		WHERE chat_role.grant_date <= CURDATE();
"""

CREATE_STATEMENTS['event role_expiration'] = """
CREATE EVENT role_expiration
    ON SCHEDULE
        EVERY 1 DAY
        STARTS CURDATE() + INTERVAL 1 DAY + INTERVAL 3 HOUR
    COMMENT 'Check expiration date of user role every day at 3 am'
    DO
        DELETE FROM chat_role WHERE CURDATE() > chat_role.expire_date;
"""


INSERT_STATEMENTS['use schema'] = """
USE `test_bot_db`;
"""
INSERT_STATEMENTS['user role'] = """
INSERT INTO role (id, name, info) VALUES (1, 'user', 'Ordinary bot user. Default role.');
"""
INSERT_STATEMENTS['admin role'] = """
INSERT INTO role (id, name, info) VALUES (2, 'admin', 'User has ascess to the bot-admin');
"""
INSERT_STATEMENTS['banned role'] = """
INSERT INTO role (id, name, info) VALUES (3, 'banned', 'User banned from using the bot');
"""

ver = sys.version_info
if ver[0] < 3 or ver[1] < 7:
    logging.warning(WARN_MSG % (ver[0], ver[1], ver[2]))