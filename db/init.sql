USE mcp_demo;

-- 0. Use the target schema to avoid cross-database issues
USE mcp_demo;

-- 1. Original tables with fixes

CREATE TABLE IF NOT EXISTS `emp` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  -- additional columns
  `date_of_birth` DATE,
  `status` ENUM('active','inactive','terminated') NOT NULL DEFAULT 'active'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `emp_profile` (
  `emp_id` INT PRIMARY KEY,
  `address` VARCHAR(255),
  `hobbies` TEXT,
  `phone` VARCHAR(20),
  -- additional columns
  `emergency_contact` VARCHAR(50),
  `linkedin` VARCHAR(255),
  CONSTRAINT `fk_emp_profile_emp`
    FOREIGN KEY (`emp_id`) REFERENCES `emp`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `emp_kpi` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `emp_id` INT,
  `kpi_name` VARCHAR(100),
  `kpi_value` DECIMAL(10,2),
  `recorded_at` DATE,
  -- additional columns
  `comments` TEXT,
  `reviewer_id` INT,
  CONSTRAINT `fk_emp_kpi_emp`
    FOREIGN KEY (`emp_id`) REFERENCES `emp`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_emp_kpi_reviewer`
    FOREIGN KEY (`reviewer_id`) REFERENCES `emp`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `role_name` VARCHAR(50) UNIQUE,
  -- additional columns
  `description` VARCHAR(255),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `emp_roles` (
  `emp_id` INT,
  `role_id` INT,
  -- additional columns
  `assigned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `approved_by` INT,
  PRIMARY KEY (`emp_id`, `role_id`),
  CONSTRAINT `fk_emp_roles_emp`
    FOREIGN KEY (`emp_id`) REFERENCES `emp`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_emp_roles_role`
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_emp_roles_approved_by`
    FOREIGN KEY (`approved_by`) REFERENCES `emp`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 2. Seed original tables with existing + expanded sample data

-- 2.1 emp (4 original + 8 new)
INSERT INTO `emp` (`name`,`email`,`password`,`date_of_birth`,`status`) VALUES
('John Doe',       'john@example.com',  'password123', '1980-01-01', 'active'),
('Jane Smith',     'jane@example.com',  'password456', '1982-02-14', 'active'),
('Alice Johnson',  'alice@example.com', 'password789', '1985-03-30', 'active'),
('Bob Brown',      'bob@example.com',   'password101', '1978-07-21', 'active'),
('Carol White',    'carol@example.com', 'passCarol1',  '1985-07-12', 'active'),
('David Black',    'david@example.com', 'passDavid2',  '1990-03-23', 'active'),
('Eve Green',      'eve@example.com',   'passEve3',    '1988-11-30', 'active'),
('Frank Yellow',   'frank@example.com', 'passFrank4',  '1979-01-05', 'active'),
('Grace Pink',     'grace@example.com', 'passGrace5',  '1992-06-17', 'active'),
('Hank Orange',    'hank@example.com',  'passHank6',   '1983-09-29', 'terminated'),
('Ivy Blue',       'ivy@example.com',   'passIvy7',    '1995-12-08', 'active'),
('Jack Violet',    'jack@example.com',  'passJack8',   '1980-04-14', 'inactive');

-- 2.2 emp_profile (profiles for IDs 1–12)
INSERT INTO `emp_profile`
  (`emp_id`,`address`,`hobbies`,`phone`,`emergency_contact`,`linkedin`)
VALUES
(1,  '123 Main St, Sydney',   'Reading',      '0412345678', '0987654321', 'https://linkedin.com/in/john'),
(2,  '456 High St, Melbourne', 'Cycling',      '0423456789', '0976543210', 'https://linkedin.com/in/jane'),
(3,  '789 Park Ave, Brisbane', 'Photography',  '0434567890', '0965432109', 'https://linkedin.com/in/alice'),
(4,  '321 King St, Perth',     'Cooking',      '0445678901', '0954321098', 'https://linkedin.com/in/bob'),
(5,  '12 Ocean St, Adelaide',  'Surfing',      '0456789012', '0943210987', 'https://linkedin.com/in/carol'),
(6,  '34 River Rd, Darwin',    'Fishing',      '0467890123', '0932109876', 'https://linkedin.com/in/david'),
(7,  '56 Mountain Dr, Hobart', 'Hiking',       '0478901234', '0921098765', 'https://linkedin.com/in/eve'),
(8,  '78 Desert Ln, Canberra', 'Photography',  '0489012345', '0910987654', 'https://linkedin.com/in/frank'),
(9,  '90 Forest Way, Townsville','Birdwatching','0490123456','0909876543','https://linkedin.com/in/grace'),
(10, '11 Lake View, Geelong',  'Boating',      '0411234567', '0898765432','https://linkedin.com/in/hank'),
(11, '22 Valley St, Ballarat', 'Cycling',      '0422345678', '0887654321','https://linkedin.com/in/ivy'),
(12, '33 Hilltop Rd, Bendigo', 'Reading',      '0433456789', '0876543210','https://linkedin.com/in/jack');

-- 2.3 emp_kpi (original + 8 new KPI records)
INSERT INTO `emp_kpi`
  (`emp_id`,`kpi_name`,`kpi_value`,`recorded_at`,`comments`,`reviewer_id`)
VALUES
(1,'Sales Target',          95.5,  '2025-04-27', 'Met target',       2),
(2,'Customer Satisfaction', 88.2,  '2025-04-28', 'Good service',     1),
(3,'Resolution Time',       1.5,   '2025-04-29', 'Excellent pace',   2),
(4,'Tickets Closed',        150.0, '2025-04-30', 'Meets target',     3),
(5,'Sales Growth',          12.5,  '2025-05-01', 'Strong growth',    1),
(6,'Support Escalations',   5.0,   '2025-05-02', 'Low escalations',   4),
(7,'New Accounts',          20.0,  '2025-05-03', 'Above average',    2),
(8,'Projects Delivered',    3.0,   '2025-05-04', 'On schedule',      3),
(9,'Training Completion Rate',100.0,'2025-05-05','All done',         1);

-- 2.4 roles (4 original + 8 new)
INSERT INTO `roles` (`role_name`,`description`) VALUES
('Admin',         'System administrator'),
('User',          'Regular user'),
('Manager',       'Team manager'),
('Guest',         'Limited access'),
('Administrator', 'Full system access'),
('Supervisor',    'Team supervision'),
('Analyst',       'Data analysis'),
('Consultant',    'External consultant'),
('Intern',        'Temporary intern'),
('Contractor',    'Contractor hire'),
('Executive',     'C-level executive'),
('Assistant',     'Administrative assistant');

-- 2.5 emp_roles (original + new role assignments)
INSERT INTO `emp_roles`
  (`emp_id`,`role_id`,`assigned_at`,`approved_by`)
VALUES
(1,1,'2025-01-01',2),(2,2,'2025-01-05',1),(3,3,'2025-01-10',2),(4,4,'2025-01-15',3),
(5, 1,'2025-02-01',1),(6, 2,'2025-02-15',2),(7, 3,'2025-03-01',3),(8, 4,'2025-03-15',4),
(9, 5,'2025-04-01',1),(10,6,'2025-04-15',2),(11,7,'2025-05-01',3),(12,8,'2025-05-15',4);

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  manager_emp_id INT,
  location VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (manager_emp_id) REFERENCES emp(id) ON DELETE SET NULL
);

INSERT INTO departments (name, manager_emp_id, location) VALUES
('Sales', 1, 'Sydney'),
('Marketing', 2, 'Melbourne'),
('Engineering', 3, 'Brisbane'),
('HR', 4, 'Perth'),
('Finance', 1, 'Sydney'),
('Support', 2, 'Melbourne'),
('R&D', 3, 'Brisbane'),
('Operations', 4, 'Perth'),
('Legal', 1, 'Sydney'),
('IT', 2, 'Melbourne');


-- 2. Projects
CREATE TABLE IF NOT EXISTS projects (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  start_date DATE,
  end_date DATE,
  budget DECIMAL(12,2),
  department_id INT,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

INSERT INTO projects (name, start_date, end_date, budget, department_id) VALUES
('Project Apollo', '2025-01-01', '2025-06-30', 500000, 3),
('Project Zeus', '2025-02-15', '2025-12-31', 750000, 3),
('Project Hera', '2025-03-01', '2025-09-30', 250000, 1),
('Project Athena', '2025-04-01', '2025-10-31', 300000, 2),
('Project Poseidon', '2025-05-01', '2025-11-30', 400000, 3),
('Project Ares', '2025-06-01', '2025-12-31', 600000, 3),
('Project Demeter', '2025-07-01', '2026-01-31', 350000, 4),
('Project Hephaestus', '2025-08-01', '2026-02-28', 450000, 3);


-- 3. emp_projects (many-to-many)
CREATE TABLE IF NOT EXISTS emp_projects (
  emp_id INT,
  project_id INT,
  assigned_at DATE,
  role VARCHAR(50),
  PRIMARY KEY (emp_id, project_id),
  FOREIGN KEY (emp_id) REFERENCES emp(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

INSERT INTO emp_projects (emp_id, project_id, assigned_at, role) VALUES
(1,1,'2025-01-05','Lead'),
(2,1,'2025-01-10','Developer'),
(3,2,'2025-02-20','Developer'),
(4,3,'2025-03-05','Analyst'),
(1,4,'2025-04-10','Coordinator'),
(2,5,'2025-05-15','Developer'),
(3,6,'2025-06-20','Tester'),
(4,7,'2025-07-25','HR Liaison');


-- 4. Attendance
CREATE TABLE IF NOT EXISTS attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  emp_id INT,
  check_in DATETIME,
  check_out DATETIME,
  status ENUM('Present','Absent','On Leave') DEFAULT 'Present',
  FOREIGN KEY (emp_id) REFERENCES emp(id) ON DELETE CASCADE
);

INSERT INTO attendance (emp_id, check_in, check_out, status) VALUES
(1,'2025-04-20 09:00','2025-04-20 17:00','Present'),
(1,'2025-04-21 09:05','2025-04-21 17:05','Present'),
(2,'2025-04-20 09:10','2025-04-20 16:00','Present'),
(2, NULL, NULL,'Absent'),
(3,'2025-04-20 09:00','2025-04-20 17:00','Present'),
(3,'2025-04-21 09:00','2025-04-21 12:00','On Leave'),
(4,'2025-04-20 09:00','2025-04-20 17:00','Present'),
(4,'2025-04-21 09:00','2025-04-21 17:00','Present');


-- 5. Leaves
CREATE TABLE IF NOT EXISTS leaves (
  id INT AUTO_INCREMENT PRIMARY KEY,
  emp_id INT,
  leave_type ENUM('Annual','Sick','Unpaid','Maternity') NOT NULL,
  start_date DATE,
  end_date DATE,
  approved_by INT,
  status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
  FOREIGN KEY (emp_id) REFERENCES emp(id) ON DELETE CASCADE,
  FOREIGN KEY (approved_by) REFERENCES emp(id) ON DELETE SET NULL
);

INSERT INTO leaves (emp_id, leave_type, start_date, end_date, approved_by, status) VALUES
(3,'Annual','2025-05-01','2025-05-05',2,'Approved'),
(2,'Sick','2025-04-22','2025-04-23',1,'Approved'),
(4,'Unpaid','2025-06-01','2025-06-10',2,'Pending'),
(1,'Maternity','2025-07-01','2025-09-30',3,'Rejected'),
(2,'Annual','2025-08-10','2025-08-15',1,'Approved'),
(3,'Sick','2025-09-05','2025-09-07',2,'Pending'),
(4,'Annual','2025-10-01','2025-10-05',1,'Approved'),
(1,'Unpaid','2025-11-01','2025-11-03',4,'Approved');


-- 6. Salaries
CREATE TABLE IF NOT EXISTS salaries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  emp_id INT,
  amount DECIMAL(12,2),
  effective_date DATE,
  note VARCHAR(255),
  FOREIGN KEY (emp_id) REFERENCES emp(id) ON DELETE CASCADE
);

INSERT INTO salaries (emp_id, amount, effective_date, note) VALUES
(1,80000,'2024-01-01','Base salary'),
(1,85000,'2025-01-01','Annual raise'),
(2,75000,'2024-02-01','Base salary'),
(2,78000,'2025-02-01','Annual raise'),
(3,90000,'2024-03-01','Base salary'),
(3,95000,'2025-03-01','Annual raise'),
(4,70000,'2024-04-01','Base salary'),
(4,73000,'2025-04-01','Annual raise');


-- 7. Benefits
CREATE TABLE IF NOT EXISTS benefits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  eligibility VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO benefits (name, description, eligibility) VALUES
('Health Insurance','Company-sponsored health plan','All Employees'),
('Dental Plan','Covers dental checkups','All Employees'),
('Retirement Plan','401(k)-style retirement saving','Employees > 1 year'),
('Wellness Program','Gym membership reimbursement','All Employees'),
('Vision Plan','Annual eye exams covered','All Employees'),
('Commuter Benefit','Pre-tax transit passes','All Employees'),
('Life Insurance','Basic life coverage','All Employees'),
('Education Reimbursement','Course fee reimbursement','Employees > 2 years');


-- 8. emp_benefits (many-to-many)
CREATE TABLE IF NOT EXISTS emp_benefits (
  emp_id INT,
  benefit_id INT,
  enrolled_at DATE,
  status ENUM('Active','Cancelled') DEFAULT 'Active',
  PRIMARY KEY(emp_id, benefit_id),
  FOREIGN KEY(emp_id) REFERENCES emp(id) ON DELETE CASCADE,
  FOREIGN KEY(benefit_id) REFERENCES benefits(id) ON DELETE CASCADE
);

INSERT INTO emp_benefits (emp_id, benefit_id, enrolled_at) VALUES
(1,1,'2024-01-15'),
(1,4,'2024-02-01'),
(2,1,'2024-02-10'),
(2,2,'2024-03-05'),
(3,3,'2024-03-20'),
(3,5,'2024-04-10'),
(4,1,'2024-04-15'),
(4,6,'2024-05-01');


-- 9. Trainings
CREATE TABLE IF NOT EXISTS trainings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150),
  provider VARCHAR(100),
  start_date DATE,
  end_date DATE,
  cost DECIMAL(10,2)
);

INSERT INTO trainings (title, provider, start_date, end_date, cost) VALUES
('Leadership 101','Udemy','2025-01-10','2025-01-15',500),
('Advanced SQL','Coursera','2025-02-05','2025-02-10',300),
('Project Mgmt','PMI','2025-03-01','2025-03-05',800),
('Time Management','LinkedIn','2025-04-01','2025-04-03',200),
('Effective Communication','edX','2025-05-10','2025-05-12',250),
('Cybersecurity Basics','Pluralsight','2025-06-01','2025-06-05',400),
('Data Analysis','DataCamp','2025-07-01','2025-07-07',350),
('Cloud Computing','AWS','2025-08-01','2025-08-05',600);


-- 10. emp_trainings (junction)
CREATE TABLE IF NOT EXISTS emp_trainings (
  emp_id INT,
  training_id INT,
  enrollment_date DATE,
  completion_status ENUM('Completed','In Progress','Not Started') DEFAULT 'Not Started',
  PRIMARY KEY(emp_id, training_id),
  FOREIGN KEY(emp_id) REFERENCES emp(id) ON DELETE CASCADE,
  FOREIGN KEY(training_id) REFERENCES trainings(id) ON DELETE CASCADE
);

INSERT INTO emp_trainings (emp_id, training_id, enrollment_date, completion_status) VALUES
(1,1,'2025-01-02','Completed'),
(1,2,'2025-02-01','Completed'),
(2,3,'2025-03-01','In Progress'),
(2,4,'2025-04-01','In Progress'),
(3,5,'2025-05-01','Not Started'),
(3,6,'2025-06-01','Not Started'),
(4,7,'2025-07-01','Not Started'),
(4,8,'2025-08-01','Not Started');


-- 11. Performance Reviews
CREATE TABLE IF NOT EXISTS performance_reviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  emp_id INT,
  reviewer_emp_id INT,
  review_date DATE,
  score INT CHECK (score BETWEEN 1 AND 5),
  comments TEXT,
  FOREIGN KEY(emp_id) REFERENCES emp(id) ON DELETE CASCADE,
  FOREIGN KEY(reviewer_emp_id) REFERENCES emp(id) ON DELETE SET NULL
);

INSERT INTO performance_reviews (emp_id, reviewer_emp_id, review_date, score, comments) VALUES
(1,2,'2025-01-15',4,'Good performance overall'),
(1,3,'2025-04-15',5,'Exceeded expectations'),
(2,1,'2025-02-20',3,'Meets requirements'),
(2,4,'2025-05-10',4,'Strong improvement'),
(3,1,'2025-03-25',5,'Excellent teamwork'),
(3,2,'2025-06-15',4,'Very proactive'),
(4,1,'2025-04-30',3,'Consistent performance'),
(4,3,'2025-07-10',5,'Outstanding contribution'),
(1,4,'2025-08-15',5,'Leadership demonstrated');