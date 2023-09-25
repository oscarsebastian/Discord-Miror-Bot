################################ IMPORTS ################################
import sys                                                             ##
import requests                                                        ##
                                                                       ##
from logger import console_output                                      ##
#########################################################################


# Define a custom exception for Discord webhook verification errors
class DiscordWebhookVerificationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        

# Define a custom exception for Discord webhook verification errors
class DiscordChannelIdVerificationError(Exception):
    def __init__(self, message):
        super().__init__(message)


def verify_discord_webhook(webhook_url: str):
    """
    Verify a Discord webhook by making an HTTP GET request to the provided URL and checking if it contains a 'token' field in the JSON response.

    Args:
        webhook_url (str): The URL of the Discord webhook to verify.

    Returns:
        bool: True if the webhook is verified, False otherwise.

    Raises:
        DiscordWebhookVerificationError: If there is an HTTP error or if the response does not contain a 'token' field.
    """
    try:
        r = requests.get(webhook_url)
        r.raise_for_status()
        r_parsed = r.json()
        if 'token' in r_parsed.keys():  
            return True
        else:
            return False
    
    except requests.exceptions.HTTPError as e:
        if 400 <= e.response.status_code < 500:
            parsed_error = e.response.json()
            # Raise the custom exception without including the original traceback
            raise DiscordWebhookVerificationError(f"Error {e.response.status_code}: {parsed_error.get('message')}") from None
        else:
            raise  # Re-raise other HTTP errors
    except requests.exceptions.RequestException as e:
        # Handle RequestException separately without trying to access e.response
        raise DiscordWebhookVerificationError(f"Request Exception: {str(e)}")
    

def verify_incognito_mode(incognito_mode: str):
    """
    Verify if the provided incognito mode is a boolean value.

    Args:
        incognito_mode (str): The value of incognito mode to be verified.

    Returns:
        bool: True if the value is a boolean, False otherwise.
    """
    # Check if the 'incognito_mode' argument is a boolean
    if isinstance(incognito_mode, bool):
        # If it is a boolean, return True, indicating a successful verification
        return True
    else:
        console_output(text=f"Incognito mode value MUST be True or False", msg_type = "ERROR")
        # If it is not a boolean, return False, indicating a verification failure
        return False


def is_float_or_int(value):
    """
    Check if a value is either a float or an int.

    Args:
        value: The value to check.

    Returns:
        bool: True if the value is a float or int, False otherwise.
    """
    valid = isinstance(value, (float, int))
    if not valid:
        console_output(text=f"Delay value MUST be an Integer or a Float", msg_type = "ERROR")
    return valid


def verify_all(
    delay,
    webhook_url: str, 
    incognito_mode: str
):
    """
    Verify multiple aspects, including Discord webhook, channel ID, and incognito mode.

    Args:
        webhook_url (str): The URL of the Discord webhook to verify.
        incognito_mode (str): The value of incognito mode to verify.

    Returns:
        bool: True if all verifications are successful, False otherwise.
    """
    try:
        # Attempt to verify the Discord webhook and store the result in 'verified_discord_webhook'
        verified_discord_webhook = verify_discord_webhook(webhook_url=webhook_url)
    except DiscordWebhookVerificationError as e:
        # If a DiscordWebhookVerificationError exception is raised during webhook verification,
        # set 'verified_discord_webhook' to False and print an error message.
        verified_discord_webhook = False
        console_output(f"Error verifying the Discord Webhook. [{e}]", msg_type = "ERROR")
        

    # Verify incognito mode by calling the 'verify_incognito_mode' function and store the result in 'verified_incognito_mode'.
    verified_incognito_mode = verify_incognito_mode(incognito_mode=incognito_mode)

    # Verify delay value is int or float
    correct_delay = is_float_or_int(value = delay)

    # Check if both verifications (webhook and incognito) are successful using 'all()'
    if all([verified_discord_webhook, verified_incognito_mode,correct_delay]):
        # If both verifications are successful, return True, indicating that all verifications passed.
        return True
    else:
        # If at least one verification fails, return False, indicating that not all verifications passed.
        return False


def verify_and_filter_tasks(task_file:dict):
    """
    Verify tasks and filter them based on verification results.

    Args:
        task_file: The file containing tasks to be verified.

    Returns:
        list: A list of tasks that have passed verification.
    """
    threaded_tasks = []  # Initialize an empty list to store verified tasks

    # Iterate through tasks in the provided task_file
    for task in task_file.to_dict('records'):
        channel_id = task.get('channel_id')
        webhook_url = task.get('webhook_url')
        incognito_mode = task.get('incognito_mode')
        delay = task.get('delay')
        
        # Verify the task using the 'verify_all' function
        is_verified = verify_all(
            webhook_url=webhook_url,
            incognito_mode=incognito_mode,
            delay = delay
        )
        
        # If the task is verified, append it to the 'threaded_tasks' list
        if is_verified:
            threaded_tasks.append(task)
        else:
            sys.exit()  # Exit the program if verification fails

    # Return the list of tasks that have passed verification
    return threaded_tasks