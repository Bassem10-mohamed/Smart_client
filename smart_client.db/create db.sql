create database smart_client;
go
use smart_client;
go

-- 1. جدول التخصصات والأسعار
create table Specialties(
    id int identity(1,1) primary key,
    name nvarchar(255) not null,
    price float not null
);

-- 2. الحسابات
create table Accounts(
    id int identity(1,1) primary key,
    name nvarchar(255) not null,
    email nvarchar(255) not null unique, -- تضمن عدم تكرار الإيميل
    role nvarchar(50) not null           -- 'Patient' أو 'Doctor'
);

-- 3. جدول الأطباء وتخصصاتهم
create table Doctors(
    id int identity(1,1) primary key,
    account_id int not null,
    specialty_id int not null,
    
    -- ربط العلاقات
    foreign key (account_id) references Accounts(id) on delete cascade,
    foreign key (specialty_id) references Specialties(id)
);

-- 4. جدول الطلبات والحجوزات المشترك
create table Appointments(
    id int identity(1,1) primary key,
    patient_id int not null,
    doctor_id int null, -- نتركه null في البداية حتى يحدده الطبيب أو النظام
    specialty_id int not null,
    appointment_date date null, -- نتركه null حتى يحدده الطبيب
    appointment_time time null, -- نتركه null حتى يحدده الطبيب
    status nvarchar(50) default 'Pending', -- يبدأ الحجز تلقائياً كـ Pending
    
    -- ربط العلاقات
    foreign key (patient_id) references Accounts(id),
    foreign key (doctor_id) references Doctors(id),
    foreign key (specialty_id) references Specialties(id)
);
