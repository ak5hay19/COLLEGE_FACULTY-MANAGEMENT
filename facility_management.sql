CREATE DATABASE IF NOT EXISTS FacilityManagement;
USE FacilityManagement;

CREATE TABLE Department (
    DepartmentID INT PRIMARY KEY AUTO_INCREMENT,
    DepartmentName VARCHAR(100) NOT NULL,
    HeadOfDepartment INT UNIQUE NULL
);

CREATE TABLE Staff (
    StaffID INT PRIMARY KEY AUTO_INCREMENT,
    StaffName VARCHAR(100) NOT NULL,
    Role VARCHAR(50),
    Email VARCHAR(100) UNIQUE,
    ContactNumber VARCHAR(15),
    DepartmentID INT,
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- Link HeadOfDepartment to Staff (1:1 via unique constraint on Department.HeadOfDepartment)
ALTER TABLE Department
ADD CONSTRAINT fk_dept_head
FOREIGN KEY (HeadOfDepartment) REFERENCES Staff(StaffID)
ON UPDATE CASCADE ON DELETE SET NULL;

CREATE TABLE FacilityType (
    FacilityTypeID INT PRIMARY KEY AUTO_INCREMENT,
    TypeName VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Facility (
    FacilityID INT PRIMARY KEY AUTO_INCREMENT,
    FacilityName VARCHAR(100) NOT NULL,
    FacilityTypeID INT,
    Location VARCHAR(100),
    Capacity INT,
    Status VARCHAR(50) DEFAULT 'Available',
    FOREIGN KEY (FacilityTypeID) REFERENCES FacilityType(FacilityTypeID)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE Equipment (
    EquipmentID INT PRIMARY KEY AUTO_INCREMENT,
    EquipmentName VARCHAR(100) NOT NULL,
    EquipmentType VARCHAR(50),
    Quantity INT DEFAULT 1,
    FacilityID INT,
    FOREIGN KEY (FacilityID) REFERENCES Facility(FacilityID)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE Maintenance (
    MaintenanceID INT PRIMARY KEY AUTO_INCREMENT,
    MaintenanceType VARCHAR(100),
    MaintenanceDate DATE,
    FacilityID INT,
    Description TEXT,
    FOREIGN KEY (FacilityID) REFERENCES Facility(FacilityID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Reservation (
    ReservationID INT PRIMARY KEY AUTO_INCREMENT,
    Purpose VARCHAR(200),
    StartTime DATETIME,
    EndTime DATETIME,
    FacilityID INT,
    StaffID INT,
    FOREIGN KEY (FacilityID) REFERENCES Facility(FacilityID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE StaffFacility (
    StaffID INT,
    FacilityID INT,
    Role VARCHAR(50),
    PRIMARY KEY (StaffID, FacilityID),
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (FacilityID) REFERENCES Facility(FacilityID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE ReservationEquipment (
    ReservationID INT,
    EquipmentID INT,
    Quantity INT DEFAULT 1,
    PRIMARY KEY (ReservationID, EquipmentID),
    FOREIGN KEY (ReservationID) REFERENCES Reservation(ReservationID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (EquipmentID) REFERENCES Equipment(EquipmentID) ON DELETE CASCADE ON UPDATE CASCADE
);

DELIMITER $$
CREATE TRIGGER trg_facility_booked
AFTER INSERT ON Reservation
FOR EACH ROW
BEGIN
    UPDATE Facility SET Status = 'Booked' WHERE FacilityID = NEW.FacilityID;
END$$

CREATE TRIGGER trg_facility_available
AFTER DELETE ON Reservation
FOR EACH ROW
BEGIN
    UPDATE Facility SET Status = 'Available' WHERE FacilityID = OLD.FacilityID;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE BookFacility(
    IN p_FacilityID INT,
    IN p_StaffID INT,
    IN p_Purpose VARCHAR(200),
    IN p_Start DATETIME,
    IN p_End DATETIME
)
BEGIN
    INSERT INTO Reservation (FacilityID, StaffID, Purpose, StartTime, EndTime)
    VALUES (p_FacilityID, p_StaffID, p_Purpose, p_Start, p_End);
END$$
DELIMITER ;

DELIMITER $$
CREATE FUNCTION CountAvailable()
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE c INT;
    SELECT COUNT(*) INTO c FROM Facility WHERE Status = 'Available';
    RETURN c;
END$$
DELIMITER ;
