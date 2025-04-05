#!/usr/bin/env python
# coding: utf-8

# In[2]:


pip install streamlit pandas matplotlib


# In[3]:


import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

# --- Database Initialization ---
def init_db():
    """Initialize the SQLite database with UserInformation and Details tables."""
    conn = sqlite3.connect('calories.db')
    c = conn.cursor()
    
    # Create UserInformation table
    c.execute('''CREATE TABLE IF NOT EXISTS UserInformation
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  email TEXT NOT NULL UNIQUE,
                  password TEXT NOT NULL)''')
    
    # Create Details table
    c.execute('''CREATE TABLE IF NOT EXISTS Details
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_email TEXT NOT NULL,
                  day1_calories INTEGER,
                  day2_calories INTEGER,
                  day3_calories INTEGER,
                  day4_calories INTEGER,
                  day5_calories INTEGER,
                  feeling_happy TEXT,
                  happy_reason TEXT,
                  food_covered TEXT,
                  other_food TEXT,
                  registration_status TEXT)''')
    
    # Set up default admin account if it doesn't exist
    admin_email = 'admin@example.com'
    admin_password = hashlib.sha256('admin'.encode()).hexdigest()
    c.execute("SELECT * FROM UserInformation WHERE email = ?", (admin_email,))
    if c.fetchone() is None:
        c.execute("INSERT INTO UserInformation (username, email, password) VALUES (?, ?, ?)",
                  ('admin', admin_email, admin_password))
    
    conn.commit()
    conn.close()

# Initialize database on script start
init_db()

# --- Session State Setup ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.is_admin = False

# --- Page Header ---
# Embed YouTube video with width 600px
st.components.v1.html(
    '<iframe width="600" height="315" src="https://www.youtube.com/embed/VEQaH4LruUo?start=65" frameborder="0" allowfullscreen></iframe>',
    height=315,
)

# Display centered title
st.markdown("<h1 style='text-align: center;'>Calories Records</h1>", unsafe_allow_html=True)

# --- Main Application Logic ---
if not st.session_state.logged_in:
    # User authentication options
    option = st.radio("Choose an option", ["Login", "Sign Up"])
    
    # --- Sign Up Page ---
    if option == "Sign Up":
        st.subheader("Sign Up")
        username = st.text_input("Username")
        email = st.text_input("Email")
        confirm_email = st.text_input("Confirm Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Submit"):
            if email != confirm_email:
                st.error("Emails do not match")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                conn = sqlite3.connect('calories.db')
                c = conn.cursor()
                c.execute("SELECT * FROM UserInformation WHERE email = ?", (email,))
                if c.fetchone() is not None:
                    st.error("Email already registered")
                else:
                    # Hash password for secure storage (despite instruction ambiguity, required for login)
                    hashed_password = hashlib.sha256(password.encode()).hexdigest()
                    c.execute("INSERT INTO UserInformation (username, email, password) VALUES (?, ?, ?)",
                              (username, email, hashed_password))
                    conn.commit()
                    st.success("Registered successfully")
                conn.close()
    
    # --- Login Page ---
    elif option == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect('calories.db')
            c = conn.cursor()
            c.execute("SELECT * FROM UserInformation WHERE email = ? AND password = ?", 
                      (email, hashed_password))
            user = c.fetchone()
            conn.close()
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.is_admin = (email == 'admin@example.com')
                st.success("Logged in successfully")
            else:
                st.error("Invalid email or password. Please register if you haven't.")
else:
    # --- Admin Dashboard ---
    if st.session_state.is_admin:
        st.subheader("Administrator Dashboard")
        conn = sqlite3.connect('calories.db')
        c = conn.cursor()
        
        # User Stats
        c.execute("SELECT COUNT(*) FROM UserInformation")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM Details WHERE registration_status = 'Registered'")
        registered_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM Details WHERE registration_status = 'Waiting List'")
        waiting_list_count = c.fetchone()[0]
        
        st.write(f"**Total Users:** {total_users}")
        st.write(f"**Registered Entries:** {registered_count}")
        st.write(f"**Waiting List Entries:** {waiting_list_count}")
        
        # Line Chart: Calorie intake per user
        c.execute("SELECT user_email, day1_calories, day2_calories, day3_calories, day4_calories, day5_calories FROM Details")
        calorie_data = c.fetchall()
        if calorie_data:
            calorie_df = pd.DataFrame(calorie_data, columns=["User", "Day1", "Day2", "Day3", "Day4", "Day5"])
            calorie_df.set_index("User", inplace=True)
            st.line_chart(calorie_df.T)
        
        # Pie Chart: Happiness proportions
        c.execute("SELECT feeling_happy, COUNT(*) FROM Details GROUP BY feeling_happy")
        happy_counts = c.fetchall()
        if happy_counts:
            labels = [row[0] for row in happy_counts]
            sizes = [row[1] for row in happy_counts]
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        
        # Happy Reasons
        c.execute("SELECT happy_reason FROM Details WHERE happy_reason != '' AND happy_reason IS NOT NULL")
        happy_reasons = [row[0] for row in c.fetchall()]
        if happy_reasons:
            st.write("**Reasons for Feeling Happy:**")
            st.write("\n".join(happy_reasons))
        
        # Food Summary Table
        c.execute("SELECT food_covered, other_food FROM Details")
        food_data = c.fetchall()
        all_foods = []
        for food_str, other in food_data:
            foods = food_str.split(',')
            if "Others" in foods and other:
                all_foods.append(other)
            all_foods.extend([f for f in foods if f != "Others"])
        food_counter = Counter(all_foods)
        if food_counter:
            food_df = pd.DataFrame(food_counter.items(), columns=["Food", "Count"])
            st.table(food_df)
        
        conn.close()
        
        # Logout Button
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.is_admin = False
    
    # --- Regular User: Calories Entry Form ---
    else:
        st.subheader("Calories Entry Form")
        with st.form("calories_form"):
            # Calorie Intake Inputs
            day1 = st.number_input("Day 1 Calories", min_value=0, value=1500)
            day2 = st.number_input("Day 2 Calories", min_value=0, value=1500)
            day3 = st.number_input("Day 3 Calories", min_value=0, value=1500)
            day4 = st.number_input("Day 4 Calories", min_value=0, value=1500)
            day5 = st.number_input("Day 5 Calories", min_value=0, value=1500)
            
            # Emotional Status
            feeling_happy = st.radio("Are you feeling happy?", ("Yes", "No"))
            happy_reason = st.text_area("What makes you feel happy?") if feeling_happy == "Yes" else ""
            
            # Food Covered Selection
            food_options = ["Rice", "Noodles", "Pasta", "Meat", "Vegetables", "Others"]
            food_covered = st.multiselect("Food Covered", food_options)
            other_food = st.text_input("Specify other food") if "Others" in food_covered else ""
            
            submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            conn = sqlite3.connect('calories.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM Details")
            total_entries = c.fetchone()[0]
            
            # Determine registration status based on total entries
            if total_entries <= 3:
                registration_status = "Registered"
                message = "Registered successfully"
            else:
                registration_status = "Waiting List"
                message = "Free quota has been reached. Please wait for the quota to reopen again."
            
            # Store data in Details table
            food_covered_str = ",".join(food_covered)
            c.execute("""INSERT INTO Details (user_email, day1_calories, day2_calories, day3_calories, 
                         day4_calories, day5_calories, feeling_happy, happy_reason, food_covered, 
                         other_food, registration_status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (st.session_state.user_email, day1, day2, day3, day4, day5, feeling_happy, 
                       happy_reason, food_covered_str, other_food, registration_status))
            conn.commit()
            conn.close()
            st.success(message)
        
        # Logout Button
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.is_admin = False


# In[ ]:




