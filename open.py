import sqlite3

def view_data():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # View students table
    c.execute('SELECT * FROM students')
    students = c.fetchall()
    print("Students Table:")
    for row in students:
        print(row)

    # View schedules table
    c.execute('SELECT * FROM schedules')
    schedules = c.fetchall()
    print("\nSchedules Table:")
    for row in schedules:
        print(row)

    # View results table
    c.execute('SELECT * FROM results')
    results = c.fetchall()
    print("\nResults Table:")
    for row in results:
        print(row)

    # Delete data 
    c.execute('DELETE FROM students')
    results= c.fetchall()
    print("Deleted Data")

    conn.close()

if __name__ == '__main__':
    view_data()
