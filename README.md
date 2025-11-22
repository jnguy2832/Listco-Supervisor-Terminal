# Listco - A Supervisor Break Management Portal

Listco is a Break Management web application designed to simplify managing break requirements and shifts of different employees.

## Features

### Break Management
- **Generate Breaks**: Generate recommended break times for employees that are scheduled
- **See who needs to be sent on break**: Provides a full list of employees and whether or not they have taken their required breaks for the day
- **Mark when employees go on break**: Mark when an employee takes their break to manage who is and isn't on break at a given time
- **See when employees breaks are over**: Marks when an employee has five minutes left in break and shows when breaks should be over
- **Mark employee's return**: Manually mark when an employee returns from break

### Shift Management
- **View weekly shifts**: See who is scheduled for each day of a given week
- **View Shift Length**: View the time frame of an employees shift for a given day
- **Employee hours**: Calculates the total hours that an employee is scheduled for in a given week

### Admin Portal
- **Login**: Super users can log in to the admin portal for elavated permissions
- **Add Employees**: Users can add employees to the application
- **Add Shifts**: Add or create shifts for employees

### Navigation
- **HomePage**: Has a central homepage to easily access different functions within the application


### How to run
- **download and unzip the .zip file in a directory of your choice**
- **Open the application folder**
- **Right click, and open a Terminal/CMD window in the application directory**
- **Run the following command prompts:**
- python -m venv my_venv
- .\my_venv\Scripts\activate <---For Windows Users
- source my_venv/bin/activate <---for macOS/Unix Users

- **Once the virtual environment is running, pip install the following plugins:**
- pip install django==5.2.7
- pip install django_q
- pip install django_q2
- pip install channels
- pip install channels_redis
- pip install daphne

- **Navigate the terminal to the /Terminal folder**
- cd Terminal

- **Run the following command: **
- python manage.py runserver

