################################ IMPORTS ################################
import os                                                              ##
import sys                                                             ##
import csv                                                             ##
import json                                                            ##
import pandas as pd                                                    ##
                                                                       ##
from logger import console_output                                      ##
#########################################################################


def open_or_create_task_csv():
    """
    This function checks if a CSV file named 'tasks.csv' exists. If it doesn't exist,
    it creates the CSV file with the specified columns and writes the header row.
    If the file already exists, it opens the CSV file and returns its contents as a DataFrame.

    Returns:
    - If the CSV file doesn't exist, it creates the file and returns None.
    - If the CSV file exists, it returns the DataFrame containing its contents.
    """
    # Define the CSV file name
    csv_file = "tasks.csv"
    
    # Define the columns for the CSV file
    columns = ["account_token_id", "channel_id", "webhook_url", "incognito_mode","delay"]

    # Check if the CSV file exists
    if not os.path.exists(csv_file):
        # If the CSV file does not exist, create it and write the header row
        with open(csv_file, mode="w", newline="") as file:
            # Create a CSV writer object
            writer = csv.DictWriter(file, fieldnames=columns)
            # Write the header row to the CSV file
            writer.writeheader()
        console_output(text = f"Created {csv_file} | Fill the file now.", msg_type='SUCCESS')
        sys.exit()
        
    else:
        # If the CSV file already exists, open it and return its contents as a DataFrame
        open_file = pd.read_csv(csv_file)
        console_output(text = f"Loaded {csv_file} succesfully.", msg_type='SUCCESS')
        return open_file


def load_custom_names_from_json():
    """
    This function loads custom names from a JSON file named 'custom_names.json' and
    returns them as a dictionary.

    Returns:
    - A dictionary containing custom names loaded from the JSON file.
    - An empty dictionary if the file does not exist or cannot be read.
    """
    if os.path.exists('custom_names.json'):
        with open('custom_names.json', 'r') as file:
            return json.load(file)
    return {}


def save_custom_names(custom_names:dict):
    """
    This function takes a dictionary of custom names and saves them to a JSON file named 'custom_names.json'.

    Parameters:
    - custom_names: A dictionary containing custom names to be saved.

    Note:
    - The function overwrites the contents of 'custom_names.json' if it already exists.
    - If the file does not exist, it will be created.

    Returns:
    - None
    """
    with open('custom_names.json', 'w') as file:
        json.dump(custom_names, file)


def record_new_message_id(
        id_value:str, 
        filename:str
):
    
    """
    This function compares a Discord message ID (id_value) with the IDs stored in a text file (filename).
    If the ID is not already in the file, it adds it and returns True.
    If the ID is already in the file, it returns False.

    Parameters:
    - id_value: The Discord message ID to compare and potentially add.
    - filename: The name of the text file where IDs are stored and checked.

    Returns:
    - True if the ID was added to the file (not already present).
    - False if the ID was already in the file.
    """
    new_id = False

    # Check if the ID is already in the file
    existing_ids = set()

    try:
        with open(filename, 'r') as file:
            existing_ids = set(line.strip() for line in file)
    except FileNotFoundError:
        # The file doesn't exist, create it (nothing to compare against)
        pass

    if id_value not in existing_ids:
        # If the ID is not in the file, add it
        with open(filename, 'a') as file:
            file.write(str(id_value) + '\n')
        new_id = True

    return new_id