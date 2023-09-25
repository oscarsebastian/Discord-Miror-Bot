################################ IMPORTS ################################                                                                                                ##
import json                                                            ##
import time                                                            ##
import random                                                          ##
import requests                                                        ##
from discord_webhook import DiscordWebhook, DiscordEmbed               ##
                                                                       ##
from logger import console_output                                      ##
#########################################################################


def fetch_discord_channel_messages(
    account_token_id: str,
    channel_id: str
):
    """
    Obtain messages from a Discord channel using the Discord API.

    Args:
        account_token_id (str): The Discord account token for authentication.
        channel_id (str): The ID of the Discord channel from which to fetch messages.

    Returns:
        list or None: A list of messages if successful, or None if there was an error.

    This function makes an HTTP GET request to the Discord API to fetch messages from a specific channel.
    It handles API response status codes and returns the fetched messages or None in case of errors.
    """
    # Generate a random sleep time between 1 and 10 seconds
    random_sleep_time = random.uniform(1, 10)

    # Define headers for the API request with authorization
    request_headers = {'authorization': account_token_id}

    # Define query parameters for the API request
    query_parameters = (('limit', '5'),)

    # Make the HTTP GET request to the Discord API
    response = requests.get(
        f'https://discord.com/api/v9/channels/{str(channel_id)}/messages',
        headers=request_headers,
        params=query_parameters
    )
    # Check the HTTP response status code
    if response.status_code == 200:
        # If the response is successful (status code 200), parse the JSON response
        messages = json.loads(response.text)
        if isinstance(messages, list):
            # If the parsed data is a list (list of messages), print a success message and return the messages
            console_output(text = "Response obtained correctly from Discord API.", msg_type = "SUCCESS")
            return messages
        else:
            # If the parsed data is not a list, return None
            return None
    elif 400 <= response.status_code < 500:
        detailed_information = "[Check input channel or account token]" if response.status_code == 404 else ''
        # If the response status code is in the 400s (client error), print an error message and the response text
        console_output(text = f"Client error {response.status_code}. {detailed_information}", msg_type = "WARNING")
    
    else:
        # If none of the above conditions are met, sleep for a random time
        console_output(text = f"Unknown error {response.status_code}.", msg_type = "WARNING")
        time.sleep(random_sleep_time)

    time.sleep(5)


def send_discord_webhook(
    message_id:str,
    webhook_url: str,
    username: str = None,
    avatar_url: str = None,
    title: str = None,
    url: str = None,
    description: str = None,
    fields: list = None,
    thumbnail: str = None,
    is_bot: bool = True,
    message_content: str = None
):
    """
    Send a Discord webhook message with optional embedded content.

    Args:
        webhook_url (str): The URL of the Discord webhook.
        username (str, optional): The username for the webhook message.
        avatar_url (str, optional): The URL of the avatar for the webhook message.
        title (str, optional): The title for the embedded content.
        url (str, optional): The URL associated with the embedded content.
        description (str, optional): The description of the embedded content.
        fields (list, optional): A list of dictionaries containing embedded fields.
        thumbnail (str, optional): The URL of the thumbnail for the embedded content.
        is_bot (bool, optional): Indicates if the message is sent by a bot (default is True).
        message_content (str, optional): The content of the message if not using embedded content.

    This function sends a Discord webhook message with optional embedded content.
    """
    if is_bot:
        webhook = DiscordWebhook(url=webhook_url, username=username, avatar_url=avatar_url)
        embed = DiscordEmbed(title=title, description=description, color='0x7b253c', url=url)
        
        if fields and len(fields) > 0:
            for field in fields:
                emb_name, emb_value = field['name'], field['value']
                embed.add_embed_field(name=emb_name, value=emb_value, inline=True)
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        webhook.add_embed(embed)
    else:
        webhook = DiscordWebhook(url=webhook_url, content=message_content, username=username, avatar_url=avatar_url)

    hook_response = webhook.execute()
    console_output(text = f"Message [{message_id}] mirrored to channel.", msg_type = "SUCCESS")
