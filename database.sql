CREATE SCHEMA `test_bot_db` DEFAULT CHARACTER SET utf8 ;
USE `test_bot_db` ;

-- tables creation
CREATE TABLE IF NOT EXISTS `book` (
    `id` SMALLINT UNSIGNED NOT NULL,
    `title` VARCHAR(1024) NULL,
    `author` VARCHAR(1024) NULL,
    `info` VARCHAR(2048) NULL,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB;


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


CREATE TABLE IF NOT EXISTS `page` (
    `book_id` SMALLINT UNSIGNED NOT NULL,
    `num` MEDIUMINT NOT NULL,
    `content` VARCHAR(4096) NULL,
    PRIMARY KEY (`book_id`, `num`),
    CONSTRAINT `fk_page_book_id`
        FOREIGN KEY (`book_id`)
        REFERENCES `book` (`id`)
) ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `role` (
    `id` INT UNSIGNED NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `info` VARCHAR(1024) NULL,
    PRIMARY KEY (`id`),
    UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE
) ENGINE = InnoDB;


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


-- create the trigger to prevent fake dates from the past
DELIMITER \\
CREATE TRIGGER `chat_role_BEFORE_INSERT` BEFORE INSERT ON `chat_role`
FOR EACH ROW
BEGIN
	IF NEW.grant_date <= CURDATE() THEN
		SET NEW.grant_date = CURDATE();
	END IF;
END \\

-- view for convenient access to user roles
CREATE OR REPLACE VIEW chat_role_view AS
    SELECT chat_id, role.name as role_name, expire_date
		FROM chat_role INNER JOIN role 
			ON chat_role.role_id = role.id
		WHERE chat_role.grant_date <= CURDATE();
        

-- create scheduler to track expiration of user roles
CREATE EVENT role_expiration
    ON SCHEDULE
        EVERY 1 DAY
        -- event starts tomorrow at 3 am
        STARTS CURDATE() + INTERVAL 1 DAY + INTERVAL 3 HOUR
    COMMENT 'Check expiration date of user role every day at 3 am'
    DO
        DELETE FROM chat_role WHERE CURDATE() > chat_role.expire_date;


INSERT INTO chat_role VALUES (chat_id, (SELECT id FROM role WHERE name = 'admin'), CURDATE(), expire_date)
