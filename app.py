from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3

app = Flask(__name__)

# Dictionary to track user states
user_states = {}

# Database setup (for simplicity using SQLite)
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    program TEXT,
                    year INTEGER,
                    signed_in INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
                    student_id TEXT,
                    day TEXT,
                    schedule TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    student_id TEXT,
                    semester TEXT,
                    gpa REAL)''')
    conn.commit()
    conn.close()

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.form.get('Body').strip().lower()
    sender_number = request.form.get('From')
    profile_name = request.form.get('ProfileName')  # Extract profile name

    response = MessagingResponse()
    message = response.message()

    # Check if the user is signed in
    if sender_number in user_states:
        state = user_states[sender_number]
    else:
        state = {'step': 'start', 'profile_name': profile_name}
        user_states[sender_number] = state

    # Process the state
    if state['step'] == 'start':
        if is_signed_in(sender_number):
            state['step'] = 'signed_in'
            message.body(f"Welcome back, {state['profile_name']}! How can I assist you today?")
        else:
            message.body(f"Welcome {profile_name}! Please enter your student ID to sign in.")
            state['step'] = 'get_student_id'
    elif state['step'] == 'get_student_id':
        state['student_id'] = incoming_msg
        message.body("Please enter your program.")
        state['step'] = 'get_program'
    elif state['step'] == 'get_program':
        state['program'] = incoming_msg
        message.body("Please enter your year.")
        state['step'] = 'get_year'
    elif state['step'] == 'get_year':
        state['year'] = incoming_msg
        sign_in_result = sign_in_student(state['student_id'], state['program'], state['year'])
        message.body(sign_in_result)
        if "successfully signed in" in sign_in_result:
            state['step'] = 'signed_in'
        else:
            state['step'] = 'start'
    elif state['step'] == 'signed_in':
        if 'schedule' in incoming_msg:
            message.body("Please provide the day for which you need the schedule. e.g., 'Schedule Monday'")
        elif 'results' in incoming_msg:
            message.body("Please provide the semester for which you need the results. e.g., 'Results Spring2023'")
        elif 'status' in incoming_msg:
            status_result = get_status(state['student_id'])
            message.body(status_result)
        else:
            message.body("Invalid command. You can ask for your 'schedule', 'results', or 'status'.")
    else:
        message.body("Please sign in first by sending your student ID.")

    return str(response)

def sign_in_student(student_id, program, year):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
    student = c.fetchone()
    if student and student[-1] == 1:
        return "You have already signed in."
    if student and student[-1] == 0:
        c.execute('UPDATE students SET signed_in = 1 WHERE student_id = ?', (student_id,))
    else:
        c.execute('INSERT INTO students (student_id, program, year, signed_in) VALUES (?, ?, ?, 1)', (student_id, program, year))
    conn.commit()
    conn.close()
    return f"Welcome {student_id}! You have successfully signed in."

def is_signed_in(sender_number):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('SELECT signed_in FROM students WHERE student_id = ?', (sender_number,))
    student = c.fetchone()
    conn.close()
    return student and student[0] == 1

def get_schedule(student_id, incoming_msg):
    parts = incoming_msg.split()
    if len(parts) < 2:
        return "Please provide the day for which you need the schedule. e.g., 'Schedule Monday'"
    
    day = parts[1].capitalize()
    
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('SELECT schedule FROM schedules WHERE student_id = ? AND day = ?', (student_id, day))
    schedule = c.fetchone()
    conn.close()
    
    if schedule:
        return f"Your schedule for {day} is: {schedule[0]}"
    else:
        return f"No schedule found for {day}."

def get_results(student_id, incoming_msg):
    parts = incoming_msg.split()
    if len(parts) < 2:
        return "Please provide the semester for which you need the results. e.g., 'Results Spring2023'"
    
    semester = parts[1]
    
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('SELECT gpa FROM results WHERE student_id = ? AND semester = ?', (student_id, semester))
    result = c.fetchone()
    conn.close()
    
    if result:
        return f"Your GPA for {semester} is: {result[0]}"
    else:
        return f"No results found for {semester}."

def get_status(student_id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('SELECT student_id, program, year FROM students WHERE student_id = ?', (student_id,))
    student = c.fetchone()
    conn.close()
    
    if student:
        return f"Student ID: {student[0]}\nProgram: {student[1]}\nYear: {student[2]}"
    else:
        return "No status found for your account."

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
