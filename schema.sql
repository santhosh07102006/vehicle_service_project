-- Vehicle Service Center Management System
-- Database Schema

CREATE DATABASE IF NOT EXISTS vehicle_service_db;
USE vehicle_service_db;

-- Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    reg_number VARCHAR(20) NOT NULL UNIQUE,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INT,
    vehicle_type ENUM('Car', 'Bike', 'Truck', 'Van', 'Other') DEFAULT 'Car',
    color VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Parts Inventory Table
CREATE TABLE IF NOT EXISTS parts (
    part_id INT AUTO_INCREMENT PRIMARY KEY,
    part_name VARCHAR(100) NOT NULL,
    part_code VARCHAR(50) UNIQUE,
    category VARCHAR(50),
    quantity INT DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL,
    supplier VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Services Table (service types offered)
CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2) NOT NULL
);

-- Bills / Service Records Table
CREATE TABLE IF NOT EXISTS bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    customer_id INT NOT NULL,
    bill_date DATE NOT NULL DEFAULT (CURDATE()),
    total_amount DECIMAL(10,2) DEFAULT 0,
    payment_status ENUM('Pending', 'Paid') DEFAULT 'Pending',
    payment_method ENUM('Cash', 'Card', 'UPI', 'Other') DEFAULT 'Cash',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Bill Items (services performed)
CREATE TABLE IF NOT EXISTS bill_service_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    service_id INT,
    custom_service_name VARCHAR(100),
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE SET NULL
);

-- Bill Items (parts used)
CREATE TABLE IF NOT EXISTS bill_part_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    part_id INT,
    custom_part_name VARCHAR(100),
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE SET NULL
);

-- Seed some default services
INSERT INTO services (service_name, description, base_price) VALUES
('Oil Change', 'Engine oil and filter replacement', 500.00),
('Wheel Alignment', 'Four-wheel alignment check and adjustment', 800.00),
('Brake Service', 'Brake pad inspection and replacement', 1200.00),
('Battery Check & Replace', 'Battery voltage test and replacement if needed', 2500.00),
('AC Service', 'AC gas refill and cooling check', 1500.00),
('General Checkup', 'Full vehicle inspection and diagnostics', 400.00);

-- Seed some default parts
INSERT INTO parts (part_name, part_code, category, quantity, unit_price, supplier) VALUES
('Engine Oil (1L)', 'OIL-001', 'Lubricants', 50, 350.00, 'Castrol India'),
('Oil Filter', 'FIL-001', 'Filters', 30, 150.00, 'Bosch India'),
('Air Filter', 'FIL-002', 'Filters', 25, 200.00, 'Bosch India'),
('Brake Pads (Set)', 'BRK-001', 'Brakes', 20, 800.00, 'Brembo India'),
('Wiper Blade', 'WIP-001', 'Accessories', 40, 250.00, 'Local Supplier'),
('Spark Plug', 'SPK-001', 'Ignition', 60, 180.00, 'NGK India');
