import pyodbc
import json
import uuid
from datetime import datetime

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=smart_client;"
    "Trusted_Connection=yes;"
)

# 1. Function to check if a user is already registered locally
def check_existing_user():
    try:
        with open("config.json", "r") as f:
            user_data = json.load(f)
            if "token" in user_data and "email" in user_data:
                return user_data
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return None

# 2. Function to fetch and display available specialties from SQL Server dynamically
def get_and_show_specialties(cursor):
    try:
        cursor.execute("SELECT id, name, price FROM Specialties")
        specialties = cursor.fetchall()
        
        if not specialties:
            print("\n⚠️ No specialties found in the database. Please add specialties first.")
            return False
            
        print("\n--- Available Specialties ---")
        for spec in specialties:
            print(f"[{spec.id}] {spec.name} - Price: {spec.price} EGP")
        return True
    except pyodbc.Error as e:
        print("Database Error fetching specialties:", e)
        return False

# 3. Function for first-time registration and database upload
def login():
    name = input("Enter your full name: ")
    email = input("Enter your email: ")
    role = input("Are you: \n1. Patient \n2. Doctor\nSelect (1 or 2): ")

    if role == "1" or role == "2":
        role_name = "Patient" if role == "1" else "Doctor"
        user_token = str(uuid.uuid4())
        specialty_id = None
        
        try:
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            # Step 3.1: If the user is a Doctor, show specialties and let them choose the ID
            if role_name == "Doctor":
                if not get_and_show_specialties(cursor):
                    cursor.close()
                    conn.close()
                    return None
                
                # Loop until a valid specialty ID is entered
                while True:
                    spec_choice = input("Enter the ID of your specialty: ")
                    cursor.execute("SELECT id FROM Specialties WHERE id = ?", (spec_choice,))
                    if cursor.fetchone():
                        specialty_id = int(spec_choice)
                        break
                    else:
                        print("❌ Invalid Specialty ID! Please choose from the list.")

            # Step 3.2: Insert user data into Accounts table (Using CONVERT for text/nvarchar safety)
            cursor.execute(
                "INSERT INTO Accounts (name, email, role) VALUES (?, ?, ?)",
                (name, email, role_name)
            )
            
            # Fetch the auto-generated ID for this new account
            cursor.execute("SELECT @@IDENTITY AS id")
            account_id = int(cursor.fetchone().id)
            
            # Step 3.3: If Doctor, fetch their actual Doctor ID from database to use later
            doctor_id = None
            if role_name == "Doctor":
                cursor.execute(
                    "INSERT INTO Doctors (account_id, specialty_id) VALUES (?, ?)",
                    (account_id, specialty_id)
                )
                cursor.execute("SELECT @@IDENTITY AS id")
                doctor_id = int(cursor.fetchone().id)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Step 3.4: Save config locally only after database insertion succeeds
            with open("config.json", "w") as f:
                user = {
                    "account_id": account_id,
                    "name" : name,
                    "email" : email,
                    "role" : role_name,
                    "token": user_token
                }
                if role_name == "Doctor":
                    user["specialty_id"] = specialty_id
                    user["doctor_id"] = doctor_id # Save doctor_id for appointment assignment
                json.dump(user, f)
            
            print(f"✅ Success! Welcome {name}. Data uploaded and token saved locally.")
            return user 
            
        except pyodbc.Error as db_err:
            print("❌ Database Setup Error:", db_err)
            return None
        except Exception as e:
            print("Error saving config file:", e)
            return None
    else:
        print("❌ Invalid choice! Please select 1 or 2.")
        return None

# --- Main Program Execution ---
print("Hello, welcome to the smart client")

# Initial check for registered user
current_user = check_existing_user()

if not current_user:
    print("\n--- First Time Setup ---")
    while True:
        current_user = login()
        if current_user:
            break

# Main Application Loop
while True:
    print(f"\nWelcome back, {current_user['name']}! Logged in as [{current_user['role']}].")
    print(f"Opening Dashboard for {current_user['role']} panel...")
    
    if current_user['role'] == "Doctor":
        # Dashboard actions for Doctor
        print("\n--- Doctor Menu ---")
        print("1. View Pending Patient Requests")
        print("2. Exit")
        doctor_choice = input("Select an option: ")
        
        if doctor_choice == "1":
            try:
                conn = pyodbc.connect(connection_string)
                cursor = conn.cursor()
                
                # Fetch pending requests matching the doctor's specialty ID
                query = """
                    SELECT a.id, acc.name 
                    FROM Appointments a
                    JOIN Accounts acc ON a.patient_id = acc.id
                    WHERE a.specialty_id = ? AND a.status = 'Pending'
                """
                cursor.execute(query, (current_user['specialty_id'],))
                pending_requests = cursor.fetchall()
                
                if not pending_requests:
                    print("\n👍 No pending patient requests in your department.")
                    cursor.close()
                    conn.close()
                else:
                    print("\n--- Pending Patient Requests ---")
                    valid_ids = []
                    for req in pending_requests:
                        print(f"Appointment ID: {req.id} | Patient Name: {req.name}")
                        valid_ids.append(int(req.id))
                    
                    # Doctor selects the Appointment ID to process
                    while True:
                        doctor_input = input("\nSelect the Appointment ID to schedule: ")
                        try:
                            chosen_app_id = int(doctor_input)
                            if chosen_app_id in valid_ids:
                                break
                            else:
                                print("❌ Invalid ID! Please choose an ID from the list above.")
                        except ValueError:
                            print("❌ Error: Please enter a valid numeric ID.")
                    
                    # Input validation for the appointment date
                    while True:
                        date_input = input("Enter appointment date (YYYY-MM-DD): ")
                        try:
                            today = datetime.today().date()
                            parsed_date = datetime.strptime(date_input, "%Y-%m-%d").date()
                            if parsed_date < today:
                                print("❌ Error: Cannot schedule appointments in the past!")
                            else:
                                break
                        except ValueError:
                            print("❌ Error: Invalid date format! Use YYYY-MM-DD.")
                    
                    # Input validation for the appointment time
                    while True:
                        time_input = input("Enter appointment time (HH:MM e.g., 14:30): ")
                        try:
                            datetime.strptime(time_input, "%H:%M")
                            break
                        except ValueError:
                            print("❌ Error: Invalid time format! Use HH:MM (24-hour format).")
                    
                    # --- Double Booking Check Logic ---
                    check_query = """
                        SELECT id FROM Appointments 
                        WHERE doctor_id = ? 
                          AND appointment_date = ? 
                          AND appointment_time = ? 
                          AND status = 'Confirmed'
                    """
                    cursor.execute(check_query, (current_user['doctor_id'], date_input, time_input))
                    is_busy = cursor.fetchone()
                    
                    if is_busy:
                        print("\n❌ Double Booking Alert! You already have a confirmed appointment at this exact time.")
                    else:
                        # Update the appointment data and change status to 'Confirmed'
                        update_query = """
                            UPDATE Appointments 
                            SET doctor_id = ?, appointment_date = ?, appointment_time = ?, status = 'Confirmed'
                            WHERE id = ?
                        """
                        cursor.execute(update_query, (current_user['doctor_id'], date_input, time_input, chosen_app_id))
                        conn.commit()
                        print("\n✅ Success! The appointment has been successfully scheduled and confirmed.")
                    
                    cursor.close()
                    conn.close()
            except pyodbc.Error as e:
                print("Database Error processing request:", e)
    

    elif current_user['role'] == "Patient":
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        Specialties = cursor.execute("select * from Specialties")
        print("\n--- send request to Doctor ---")
        valid_ids = []
        for reg in Specialties:
            print(f"id Specialties {reg.id} || name Specialties {reg.name} || price Specialties {reg.price}")
            valid_ids.append(int(reg.id))

      # Doctor selects the Appointment ID to process
        while True:
            patient_input = input("\nSelect the Specialties ID to send request: ")
            try:
               chosen_app_id = int(patient_input)
               if chosen_app_id in valid_ids:
                break
               else:
                print("❌ Invalid ID! Please choose an ID from the list above.")
            except ValueError:
                print("❌ Error: Please enter a valid ID.")