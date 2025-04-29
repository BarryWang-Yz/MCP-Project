CREATE TABLE IF NOT EXISTS `emp` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `emp_profile` (
    `emp_id` INT PRIMARY KEY,
    `address` VARCHAR(255),
    `hobbies` TEXT,
    `phone` VARCHAR(20),
    FOREIGN KEY (`emp_id`) REFERENCES `emp`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `emp_kpi` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `emp_id` INT,
    `kpi_name` VARCHAR(100),
    `kpi_value` DECIMAL(10,2),
    `recorded_at` DATE,
    FOREIGN KEY (`emp_id`) REFERENCES `emp`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `role_name` VARCHAR(50) UNIQUE
);

CREATE TABLE IF NOT EXISTS `emp_roles` (
    `emp_id` INT,
    `role_id` INT,
    PRIMARY KEY (`emp_id`, `role_id`),
    FOREIGN KEY (`emp_id`) REFERENCES `emp`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
);

INSERT INTO `emp` (`name`, `email`, `password`) VALUES
('John Doe', 'john@example.com', 'password123'),
('Jane Smith', 'jane@example.com', 'password456'),
('Alice Johnson', 'alice@example.com', 'password789'),
('Bob Brown', 'bob@example.com', 'password101');

-- Assuming the inserted emp has id = 1
-- Insert into emp_profile
INSERT INTO `emp_profile` (`emp_id`, `address`, `hobbies`, `phone`) VALUES
(1, '123 Main St, Sydney', 'Reading', '0412345678'),
(2, '456 High St, Melbourne', 'Cycling', '0423456789'),
(3, '789 Park Ave, Brisbane', 'Photography', '0434567890'),
(4, '321 King St, Perth', 'Cooking', '0445678901');

-- Sample data for 'emp_kpi'
INSERT INTO `emp_kpi` (`emp_id`, `kpi_name`, `kpi_value`, `recorded_at`) VALUES
(1, 'Sales Target', 95.5, '2025-04-27');