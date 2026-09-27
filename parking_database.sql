CREATE TABLE Vehicles (
    vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    number_plate VARCHAR(15) NOT NULL UNIQUE,
    vehicle_type VARCHAR(20),
    phone_number VARCHAR(15)
);

CREATE TABLE Parking_slots(
    slot_id INT PRIMARY KEY AUTO_INCREMENT,
    slot_no VARCHAR(3) NOT NULL UNIQUE,
    slot_zone VARCHAR(1),
    slot_status ENUM('FREE','OCCUPIED') DEFAULT 'FREE'
);

CREATE TABLE Tickets(
    ticket_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id INT NOT NULL,
    slot_id INT NOT NULL,
    entry_time TIMESTAMP NOT NULL DEFAULT NOW(),
    exit_time TIMESTAMP NULL,
    ticket_status ENUM('ACTIVE','CLOSED') DEFAULT 'ACTIVE',
    FOREIGN KEY (vehicle_id) REFERENCES Vehicles(vehicle_id),
    FOREIGN KEY (slot_id) REFERENCES Parking_slots(slot_id)    
);
 
 CREATE INDEX idx_active_ticets ON Tickets(vehicle_id, ticket_status);

CREATE TABLE Tariffs(
    tariff_band_id INT PRIMARY KEY AUTO_INCREMENT,
    min_minutes INT NOT NULL,
    max_minutes INT NOT NULL,
    fee DECIMAL(10,2) NOT NULL CHECK (fee >= 0),
    description VARCHAR(100) NOT NULL,
    CONSTRAINT tariff_validity CHECK (min_minutes < max_minutes)
);

CREATE TABLE Payment(
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_id INT NOT NULL,
    tariff_band_id INT NOT NULL,
    duration_min INT NOT NULL,
    amount_due DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    payment_method ENUM('CASH','MPESA','CARD') DEFAULT 'CASH',
    payment_status ENUM('PENDING','CONFIRMED','REJECTED') DEFAULT 'PENDING',
    payment_time TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id),
    FOREIGN KEY (tariff_band_id) REFERENCES Tariffs(tariff_band_id),
    CONSTRAINT sufficient CHECK (amount_paid >= amount_due)
);

CREATE TABLE Users(
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(60) NOT NULL UNIQUE,
    user_password VARCHAR(225) NOT NULL,
    user_role VARCHAR(20) NOT NULL CHECK (user_role IN ('ADMIN','ATTENDANT'))
);

CREATE TABLE Audit_Log(
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    action VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    log_time TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

--Data entered into the dynamic database.

INSERT INTO Tariffs (min_minutes, max_minutes, fee, description) VALUES
(0, 30, 0.00, 'Up to 30 minutes is FREE'),   
(31, 120, 50.00, '31 minutes to 2 hours'),
(121, 240, 100.00, 'Over 2 hours to 4 hours'),
(241, 360, 300.00, 'Over 4 hours to 6 hours'),
(361, 99999, 500.00, 'Over 6 hours');

INSERT INTO Parking_slots (slot_no, slot_zone) VALUES
('A1','A'),('A2','A'),('A3','A'),('A4','A'),('A5','A'),('A6','A'),('A7','A'),('A8','A'),('A9','A'),('A10','A'),
('B1','B'),('B2','B'),('B3','B'),('B4','B'),('B5','B'),('B6','B'),('B7','B'),('B8','B'),('B9','B'),('B10','B'),
('C1','C'),('C2','C'),('C3','C'),('C4','C'),('C5','C'),('C6','C'),('C7','C'),('C8','C'),('C9','C'),('C10','C'),
('D1','D'),('D2','D'),('D3','D'),('D4','D'),('D5','D'),('D6','D'),('D7','D'),('D8','D'),('D9','D'),('D10','D');


