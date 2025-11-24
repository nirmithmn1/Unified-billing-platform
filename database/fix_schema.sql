-- First, drop the trigger if it exists
DROP TRIGGER IF EXISTS after_user_update;

-- Fix the trigger with proper DELIMITER
DELIMITER //
CREATE TRIGGER after_user_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (
        user_id,
        action,
        table_name,
        record_id,
        old_values,
        new_values
    )
    VALUES (
        NEW.id,
        'UPDATE',
        'users',
        NEW.id,
        CONCAT(
            '{"username":"', OLD.username, 
            '","email":"', IFNULL(OLD.email, ''), 
            '","role":"', OLD.role, 
            '","is_active":', IF(OLD.is_active, 'true', 'false'), '}'
        ),
        CONCAT(
            '{"username":"', NEW.username, 
            '","email":"', IFNULL(NEW.email, ''), 
            '","role":"', NEW.role, 
            '","is_active":', IF(NEW.is_active, 'true', 'false'), '}'
        )
    );
END; //

-- Reset delimiter
DELIMITER ;