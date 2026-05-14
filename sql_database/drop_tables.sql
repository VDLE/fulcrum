DELIMITER $$

CREATE PROCEDURE drop_all_tables() 
BEGIN
    DECLARE _done INT DEFAULT FALSE;
    DECLARE _tableName VARCHAR(255);
    DECLARE _cursor CURSOR FOR
        SELECT table_name
        FROM information_schema.TABLES
        WHERE table_schema = 'DEVELOP_fulcrum';

    -- Ensure you're using the correct schema name
    DECLARE CONTINUE HANDLER FOR NOT FOUND
    SET _done = TRUE;

    SET FOREIGN_KEY_CHECKS = 0;  -- Disable foreign key checks to avoid constraint errors

    OPEN _cursor;

    REPEAT
        FETCH _cursor INTO _tableName;

        IF NOT _done THEN
            SET @stmt_sql = CONCAT('DROP TABLE ', _tableName);
            PREPARE stmt1 FROM @stmt_sql;
            EXECUTE stmt1;
            DEALLOCATE PREPARE stmt1;
        END IF;
    UNTIL _done
    END REPEAT;

    CLOSE _cursor;

    SET FOREIGN_KEY_CHECKS = 1;  -- Enable foreign key checks

END $$

DELIMITER ;

-- Call the procedure to drop all tables
CALL drop_all_tables();

-- Optionally, drop the procedure after use
DROP PROCEDURE IF EXISTS `drop_all_tables`;
