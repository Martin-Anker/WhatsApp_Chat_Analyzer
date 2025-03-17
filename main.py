import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import re
import csv
import zipfile
import os
import matplotlib.dates as mdates
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog
from matplotlib.dates import MonthLocator, DateFormatter
from textblob import TextBlob

#--------------------------------------------
#System variables
#--------------------------------------------


window = None
owner_name = "Martin"

def parse_message(line):
    # Regex für das Format: "31.01.25, 02:17 - Absender: Nachricht"
    pattern = r"(\d{2}\.\d{2}\.\d{2}), (\d{2}:\d{2}) - (.+?): (.+)"
    
    match = re.match(pattern, line.strip())
    if match:
        date = match.group(1)
        time = match.group(2)
        sender = match.group(3)
        message = match.group(4)
        return (date, time, sender, message)
    return None

def convert_txt_to_csv(chat_label, input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Liste für die extrahierten Nachrichten
    messages = []
    
    current_message = []
    current_date = current_time = current_sender = ""
    
    for line in lines:
        
        #skip first two lines (whatsapp info messages)
        if lines.index(line) < 2:
            continue

        parsed = parse_message(line)
        if parsed:
            # Wenn eine neue Nachricht erkannt wurde, speichern wir die alte Nachricht
            if current_message:
                messages.append((chat_label, current_date, current_time, current_sender, "".join(current_message)))
            
            # Aktuelle Nachricht setzen
            current_date, current_time, current_sender, message = parsed
            current_message = [message]  # Nachricht starten

        else:
            # Falls es keine neue Nachricht ist, fügen wir den Text zur aktuellen Nachricht hinzu
            current_message.append(line.strip())
    
    # Letzte Nachricht hinzufügen (falls vorhanden)
    if current_message:
        messages.append((chat_label, current_date, current_time, current_sender, "".join(current_message)))
    
    # Schreiben in die CSV-Datei
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Chat", "Datum", "Uhrzeit", "Absender", "Nachricht"])
        for message in messages:
            csv_writer.writerow(message)

def merge_csv_files(csv_folder, output_file):
    # List to hold all rows of data
    all_rows = []

    # Go through each file in the folder
    for file_name in os.listdir(csv_folder):
        file_path = os.path.join(csv_folder, file_name)

        # Only process CSV files
        if file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                # Skip header in all but the first file
                header = next(csv_reader)  # Read the header

                # If this is the first file, add the header to the output file
                if not all_rows:
                    all_rows.append(header)
                
                # Append rows from the current CSV file
                for row in csv_reader:
                    all_rows.append(row)

    # Write all the rows to the output file
    with open(output_file, 'w', newline='', encoding='utf-8') as output:
        csv_writer = csv.writer(output)
        # Write all rows
        csv_writer.writerows(all_rows)

def prepare_data():
    data_folder = './chat_data'
    csv_folder = './csv_data'

    os.makedirs(data_folder, exist_ok=True)
    os.makedirs(csv_folder, exist_ok=True)

    for file_name in os.listdir(data_folder):
        file_path = os.path.join(data_folder, file_name)
        
        # Überprüfen, ob die Datei eine ZIP-Datei ist
        if zipfile.is_zipfile(file_path):
            # Erstelle einen Ordner zum Entpacken
            extract_folder = os.path.join(data_folder, file_name.replace('.zip', '_extracted'))
            os.makedirs(extract_folder, exist_ok=True)

            # Entpacke die ZIP-Datei
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            
            # Durchlaufe die entpackten Dateien und suche nach einer Textdatei
            for extracted_file in os.listdir(extract_folder):
                extracted_file_path = os.path.join(extract_folder, extracted_file)
                if extracted_file.endswith('.txt'):
                    # Konvertiere die Textdatei in eine CSV-Datei
                    output_file = extracted_file.replace('.txt', '.csv')
                    label = input("Enter the name of the chat - " + file_name.replace('.zip', '') + ": ")
                    #label = file_name.replace('WhatsApp-Chat mit ', '').replace('.zip', '')
                    convert_txt_to_csv(label, extracted_file_path, os.path.join(csv_folder, output_file))

            #remove all extracted files
            for extracted_file in os.listdir(extract_folder):
                extracted_file_path = os.path.join(extract_folder, extracted_file)
                os.remove(extracted_file_path)
            os.rmdir(extract_folder)
    merge_csv_files(csv_folder, './all_chats.csv')

def is_emoji(character):
    try:
        # Check if the character is in a known emoji Unicode range
        # Unicode ranges for emojis
        if '\U0001F600' <= character <= '\U0001F64F' or \
           '\U0001F300' <= character <= '\U0001F5FF' or \
           '\U0001F680' <= character <= '\U0001F6FF' or \
           '\U0001F700' <= character <= '\U0001F77F' or \
           '\U0001F780' <= character <= '\U0001F7FF' or \
           '\U0001F800' <= character <= '\U0001F8FF' or \
           '\U0001F900' <= character <= '\U0001F9FF' or \
           '\U0001FA00' <= character <= '\U0001FA6F' or \
           '\U0001FA70' <= character <= '\U0001FAFF' or \
           '\U00002702' <= character <= '\U000027B0' or \
           '\U000024C2' <= character <= '\U0001F251':
            return True
        return False
    except TypeError:
        return False

def choose_users():
    users = []
    input_string = simpledialog.askstring("Input", "Enter the names of the users to analyse separated by a comma (leave empty for all):", parent=window)
    if input_string != "":
        users = input_string.split(',')
        for i in range(len(users)):
            users[i] = users[i].strip()
    else:
        users = pd.read_csv('all_chats.csv')['Chat'].unique()
    return users

#Analysis functions 
def analyse_message_amount():
    #Make bar chart of message amount
    df = pd.read_csv('all_chats.csv')

    df_other = df[df['Absender'] != owner_name]
    df_owner = df[df['Absender'] == owner_name]

    # Count the number of messages for each sender
    message_counts_other = df_other['Chat'].value_counts()
    message_counts_owner = df_owner['Chat'].value_counts()

    # Create a bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.bar(message_counts_other.index, message_counts_other.values)
    ax.bar(message_counts_owner.index, message_counts_owner.values, bottom=message_counts_other.values)

    # Add labels and title
    ax.set_xlabel('Chat')
    ax.set_ylabel('Message Count')
    ax.set_title('Message Count by Sender for Each Chat')

    ax.legend(title="Sender", labels=['Other', owner_name])

    # Display the plot
    plt.tight_layout()
    plt.show()

def analyse_message_frequency():
    #name = simpledialog.askstring("Input", "Enter the name of the person whose chat you want to analyse:", parent=window)
    names = choose_users()

    #Read data from all_chats.csv and import into pandas
    df = pd.read_csv('all_chats.csv')

    # Ensure the 'Datum' (Date) column is in datetime format
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%y')

    # Create a new column that represents two-month intervals
    df['Two_Month_Interval'] = df['Datum'].apply(lambda x: pd.Timestamp(datetime(x.year, ((x.month-1)//1)*1+1, 1)))

    # Extract the month and year from the 'Datum' column
    #df['Month_Year'] = df['Datum'].dt.to_period('M')

    # Group by 'Month_Year' and 'Absender' (sender) and count the messages
    message_counts = df.groupby(['Two_Month_Interval', 'Chat']).size().reset_index(name='Message_Count')

    # Create a plot for each sender
    plt.figure(figsize=(10, 6))

    # Filter the data for a specific sender
    message_counts = message_counts[message_counts['Chat'].isin(names)]

    # We will create a line for each sender showing the number of messages per month
    for sender in message_counts['Chat'].unique():
        sender_data = message_counts[message_counts['Chat'] == sender]
        plt.plot(sender_data['Two_Month_Interval'], sender_data['Message_Count'], label=sender)

    # Format the x-axis to show the timeline
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    plt.axhline(0, color='grey', linewidth=1, linestyle='--')
    # Rotate the labels for readability
    plt.xticks(rotation=45)

    # Add labels and title
    plt.xlabel('Month')
    plt.ylabel('Number of Messages')
    plt.title('Timeline of Messages by Chat (Fist Message - Present)')
    plt.legend(title='Sender')

    # Display the plot
    plt.tight_layout()
    plt.show()

def analyse_message_length():
    #Read data from all_chats.csv and import into pandas
    df = pd.read_csv('all_chats.csv')

    df['Nachricht'] = df['Nachricht'].astype(str)

    df_other = df[df['Absender'] != owner_name]
    df_owner = df[df['Absender'] == owner_name]

    # Calculate the length of each message
    df_other['Message_Length'] = df_other['Nachricht'].apply(lambda x: len(x))
    df_owner['Message_Length'] = df_owner['Nachricht'].apply(lambda x: len(x))

    # Group by 'Absender' (sender) and calculate the average message length
    avg_message_length_other = df_other.groupby('Chat')['Message_Length'].mean()
    avg_message_length_owner = df_owner.groupby('Chat')['Message_Length'].mean()

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define the width of each bar
    bar_width = 0.35

    # Define the x positions for the bars
    index = np.arange(len(df['Chat'].unique()))

    # Plot the bars for Sender1 and Sender2
    ax.bar(index - bar_width/2, avg_message_length_other.values, bar_width, label='Other')  # Bar for Sender1
    ax.bar(index + bar_width/2, avg_message_length_owner.values, bar_width, label=owner_name)  # Bar for Sender2

    # Add labels and title
    ax.set_xlabel('Chat')
    ax.set_ylabel('Message Length by Characters')
    ax.set_title('Message Length by Sender')
    ax.set_xticks(index)  # Set x-axis tick positions
    ax.set_xticklabels(df['Chat'].unique())  # Set x-axis tick labels to the Chat names

    # Add the legend
    ax.legend(title="Senders")

    # Display the plot
    plt.tight_layout()
    plt.show()

def analyse_emoji():
    chat_filter = choose_users()

    df = pd.read_csv('all_chats.csv')

    df = df[df['Chat'].isin(chat_filter)]

    df['Nachricht'] = df['Nachricht'].astype(str)

    # make a piechart of the type of emojis used
    emoji_counts = {}

    for message in df['Nachricht']:
        for character in message:
            if is_emoji(character):
                if character in emoji_counts:
                    emoji_counts[character] += 1
                else:
                    emoji_counts[character] = 1
    
    # Sort the emojis by count
    sorted_emojis = sorted(emoji_counts.items(), key=lambda x: x[1], reverse=True)

    # Create a pie chart
    plt.figure(figsize=(10, 6))
    labels = []
    sizes = []

    for emoji, count in sorted_emojis:
        labels.append(emoji)
        sizes.append(count)

    # Only show the top 15 emojis
    labels = labels[:10] + ['Others']
    sizes = sizes[:10] + [sum(sizes[15:])]

    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 14})
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Add title
    plt.title('Emoji Distribution in Chat: ' + chat_filter)

    plt.rcParams['font.family'] = 'Segoe UI Emoji' 

    # Display the plot
    plt.tight_layout()
    plt.show()

def last_message_of_conversation():
    chat_filter = choose_users()

    df = pd.read_csv('all_chats.csv')

    df = df[df['Chat'].isin(chat_filter)]

    #Group by day and chat
    df = df.groupby(['Datum'])

def answer_deviation():
    chat_filter = choose_users()

    df = pd.read_csv('all_chats.csv')

    # Ensure the 'Datum' (Date) column is in datetime format
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%y')

    df = df[df['Chat'].isin(chat_filter)]

    df["random_walk"] = df["Absender"].apply(lambda x: -1 if x == owner_name else 1)

    df["random_walk"] = df["random_walk"].cumsum()

    plt.figure(figsize=(10, 6))

    plt.axhline(0, color='grey', linewidth=1, linestyle='--')

    plt.plot(df["Datum"], df["random_walk"])
    plt.title("Answer Deviation")
    plt.xlabel("Date")
    plt.ylabel("Answer Deviation")

    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # Rotate and spread out the x-axis date labels
    plt.xticks(rotation=45, ha='right')  # Rotate labels by 45 degrees for readability

    plt.tight_layout()
    plt.show()

def time_of_day_analysis():
    chat_filter = choose_users()

    df = pd.read_csv('all_chats.csv')

    df = df[df['Chat'].isin(chat_filter)]

    df['Uhrzeit'] = pd.to_datetime(df['Uhrzeit'], format='%H:%M')

    # Extract the hour from the 'Uhrzeit' column
    df['Hour'] = df['Uhrzeit'].dt.hour

    # Group by 'Hour' and 'Absender' (sender) and count the messages
    message_counts = df.groupby(['Hour', 'Chat']).size().reset_index(name='Message_Count')

    # Create a plot for each sender
    plt.figure(figsize=(10, 6))

    # Filter the data for a specific sender
    message_counts = message_counts[message_counts['Chat'] == chat_filter]

    # We will create a line for each sender showing the number of messages per hour
    for sender in message_counts['Chat'].unique():
        sender_data = message_counts[message_counts['Chat'] == sender]
        plt.plot(sender_data['Hour'], sender_data['Message_Count'], label=sender)

    # Add labels and title
    plt.xlabel('Hour of the Day')
    plt.xticks(range(0, 24, 2))  # Show every second hour
    plt.ylabel('Number of Messages')
    plt.title('Time of Day Analysis of Messages - Chat: ' + chat_filter)

    # Display the plot
    plt.tight_layout()
    plt.show()

def sentiment_analysis():

    df = pd.read_csv('all_chats.csv')

    df['Nachricht'] = df['Nachricht'].astype(str)

    df_other = df[df['Absender'] != owner_name]
    df_owner = df[df['Absender'] == owner_name]

    #TODO: Does this makes sense?
    #filter out messages with high objectivity (since they dont really matter for polarity)
    df_other = df_other[df_other['Nachricht'].apply(lambda x: TextBlob(x).sentiment.subjectivity) < 0.5]
    df_owner = df_owner[df_owner['Nachricht'].apply(lambda x: TextBlob(x).sentiment.subjectivity) < 0.5]

    # Calculate the length of each message
    df_other['Sentiment'] = df_other['Nachricht'].apply(lambda x: TextBlob(x).sentiment.polarity)
    df_owner['Sentiment'] = df_owner['Nachricht'].apply(lambda x: TextBlob(x).sentiment.polarity)

    # Group by 'Absender' (sender) and calculate the average message length
    avg_sentiment_other = df_other.groupby('Chat')['Sentiment'].mean()
    avg_sentiment_owner = df_owner.groupby('Chat')['Sentiment'].mean()

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define the width of each bar
    bar_width = 0.35

    # Define the x positions for the bars
    index = np.arange(len(df['Chat'].unique()))

    # Plot the bars for Sender1 and Sender2
    ax.bar(index - bar_width/2, avg_sentiment_other.values, bar_width, label='Other')
    ax.bar(index + bar_width/2, avg_sentiment_owner.values, bar_width, label=owner_name)

    # Add labels and title
    ax.set_xlabel('Chat')
    ax.set_ylabel('Average Sentiment')
    ax.set_title('Average Sentiment by Sender')
    ax.set_xticks(index)  # Set x-axis tick positions
    ax.set_xticklabels(df['Chat'].unique())  # Set x-axis tick labels to the Chat names

    # Add the legend
    ax.legend(title="Senders")

    # Display the plot
    plt.tight_layout()
    plt.show()

def own_message_frequency():
    df = pd.read_csv('all_chats.csv')

    df = df[df['Absender'] == owner_name]

    # Ensure the 'Datum' (Date) column is in datetime format
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%y')

    # Create a new column that represents month intervals
    df['Two_Month_Interval'] = df['Datum'].apply(lambda x: pd.Timestamp(datetime(x.year, ((x.month-1)//1)*1+1, 1)))

    # Group by 'Month_Year' and 'Absender' (sender) and count the messages
    message_counts = df.groupby('Two_Month_Interval').size().reset_index(name='Message_Count')

    # Create a plot for each sender
    plt.figure(figsize=(10, 6))

    plt.plot(message_counts['Two_Month_Interval'], message_counts['Message_Count'])

    # Format the x-axis to show the timeline
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    plt.axhline(0, color='grey', linewidth=1, linestyle='--')
    # Rotate the labels for readability
    plt.xticks(rotation=45)

    # Add labels and title
    plt.xlabel('Month')
    plt.ylabel('Number of Messages')
    plt.title('Timeline of Messages by ' + owner_name +' (Fist Message - Present)')

    # Display the plot
    plt.tight_layout()
    plt.show()
#--------------------------------------------

def on_prepare_data():
    print("Data preparation started...")
    prepare_data()
    print("Data preparation completed.")

def detect_owner_name():
    df = pd.read_csv('all_chats.csv')
    df = df.groupby('Chat')['Absender'].unique().reset_index()

    common_elements = set(df['Absender'].iloc[0])  # Start with the first row's set
    for senders in df['Absender']:
        common_elements.intersection_update(senders)  # Keep only elements present in all rows
    return common_elements.pop()  # Return the only element left

def on_analysis_mode(mode):
    if mode == "Message Amount":
        analyse_message_amount()
    elif mode == "Message Frequency":
        analyse_message_frequency()
    elif mode == "Average Message Length":
        analyse_message_length()
    elif mode == "Emoji Analysis":
        analyse_emoji()
    elif mode == "Answer Deviation":
        answer_deviation()
    elif mode == "Last Message of Conversaion":
        pass
    elif mode == "Time of Day Analysis":
        time_of_day_analysis()
    elif mode == "Sentiment Analysis":
        sentiment_analysis()
    elif mode == "Own Message Frequency":
        own_message_frequency()

def create_window():
    # Create the main window
    window = tk.Tk()
    window.title("Data Analysis Tool")

    # Create a "Prepare Data" button at the top
    prepare_button = tk.Button(window, text="Prepare Data", command=on_prepare_data)
    prepare_button.pack(pady=10)

    # Create a label for the instruction text
    instruction_label = tk.Label(window, text="Select analysis mode from below.")
    instruction_label.pack(pady=5)

    # Create a frame to hold the mode buttons
    mode_frame = tk.Frame(window)
    mode_frame.pack(pady=10)

    # List of analysis modes
    modes = ["Message Amount", "Message Frequency", "Average Message Length", "Emoji Analysis", "Answer Deviation", "Last Message of Conversaion", "Time of Day Analysis", "Sentiment Analysis", "Own Message Frequency"]

    # Create a button for half of the analysis modes
    for mode in modes:
        mode_button = tk.Button(mode_frame, text=mode, command=lambda m=mode: on_analysis_mode(m))
        mode_button.pack(side=tk.LEFT, padx=10)

    # Run the Tkinter event loop
    window.mainloop()

if __name__ == "__main__":
    owner_name = detect_owner_name()
    create_window()

