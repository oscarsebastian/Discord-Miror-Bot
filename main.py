################################ IMPORTS ################################
import time                                                            ## 
import threading                                                       ##
                                                                       ##
from logger import console_output                                      ##
from utils import discord_utils,file_utils,verification_utils          ##
#########################################################################


def hide_discord_username(
    username: str, 
    incognito_names: dict
):
    """
    Hide a Discord username using an incognito names dictionary.

    Args:
        username (str): The original Discord username.
        incognito_names (dict): A dictionary mapping original usernames to incognito names.

    Returns:
        str: The hidden or incognito username.
    """
    if username not in incognito_names:
        incognito_names[username] = f'user{len(incognito_names) + 1}'

    hidden_username = incognito_names[username]
    
    # Save the modified incognito_names dictionary to a JSON file
    file_utils.save_custom_names(custom_names=incognito_names)
    
    return hidden_username


def extract_embedded_data(embedded_list: list):
    """
    Extract data from a list of embedded messages.

    Args:
        embedded_list (list): A list of embedded messages.

    Returns:
        tuple: A tuple containing extracted data (embed_type, title, url, description, fields, thumbnail).
    """
    for embed in embedded_list:
        embed_type = embed.get('type')
        title = embed.get('title')
        url = embed.get('url')
        description = embed.get('description')
        fields = embed.get('fields')
        thumbnail_url = embed.get('thumbnail', {}).get('url')

        return embed_type, title, url, description, fields, thumbnail_url


def monitor_discord_api(
    delay:float,
    account_token_id: str,
    channel_id: str,
    webhook_url: str,
    incognito_mode: bool = False
):
    """
    Monitor a Discord API for new messages and send them to a webhook.

    Args:
        account_token_id (str): The Discord account token for authentication.
        channel_id (str): The ID of the Discord channel to monitor.
        webhook_url (str): The URL of the Discord webhook to send messages to.
        incognito_mode (bool, optional): Indicates if usernames should be hidden (default is False).
    """
    while True:
        messages = discord_utils.fetch_discord_channel_messages(
            account_token_id = account_token_id, 
            channel_id = channel_id
        )
        incognito_names = file_utils.load_custom_names_from_json()
        
        if messages:
            for message in messages:
                message_id = message.get('id')
                new_message = file_utils.record_new_message_id(
                    id_value = message_id, 
                    filename = 'ids.txt'
                )
                
                username = message.get('author').get('username')
                message_content = message.get('content')
                embeds = message.get('embeds')
                
                if not new_message:
                    console_output(f"Message [{message_id}] already mirrored.",msg_type="INFO")
                else:
                    console_output(f"New message [{message_id}] detected.",msg_type="SUCCESS")
                    if incognito_mode:
                        username = hide_discord_username(username, incognito_names)
                        avatar_link = None
                    else:
                        author = message.get('author')
                        username = author.get('username')
                        avatar = author.get('avatar')
                        auth_id = author.get('id')
                        avatar_link = f"https://cdn.discordapp.com/avatars/{auth_id}/{avatar}.png"
                    
                    if embeds and len(embeds) > 0:
                        embed_type, title, url, description, fields, thumbnail = extract_embedded_data(embedded_list=embeds)

                        if embed_type == 'rich' and fields:
                            console_output(text = f"Webhook detected on channel [{channel_id}].",msg_type = "INFO")
                            discord_utils.send_discord_webhook(
                                message_id = message_id,
                                username=username,
                                avatar_url=avatar_link,
                                webhook_url=webhook_url,
                                title=title,
                                url=url,
                                description=description,
                                fields=fields,
                                thumbnail=thumbnail
                            )
                        else:
                            discord_utils.send_discord_webhook(
                                message_id = message_id,
                                username=username,
                                is_bot=False,
                                webhook_url=webhook_url,
                                message_content=message_content
                            )
                    else:
                        discord_utils.send_discord_webhook(
                            message_id = message_id,
                            username=username,
                            avatar_url=avatar_link,
                            is_bot=False,
                            webhook_url=webhook_url,
                            message_content=message_content
                        )

            console_output(text = f"No new messages on channel [{channel_id}] | Sleeping for [{delay}]s.",msg_type = "INFO")
            time.sleep(delay)

if __name__ == '__main__':
    threads = []

    tasks = file_utils.open_or_create_task_csv()
    tasks_to_run = verification_utils.verify_and_filter_tasks(task_file = tasks)
    for task in tasks_to_run:
        account_token_id = task.get('account_token_id')
        channel_id = str(task.get('channel_id'))
        webhook_url = task.get('webhook_url')
        delay = task.get('delay')
        incognito_mode = task.get('incognito_mode')

        thread = threading.Thread(target=monitor_discord_api, args=(delay,account_token_id, channel_id, webhook_url, incognito_mode))
        threads.append(thread)
        thread.start()

