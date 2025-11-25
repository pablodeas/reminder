#! /usr/bin/env python3

#   Author:         Pablo Andrade
#   Created:        29/11/2024
#   Version:        0.0.3
#   Objective:      Program to send Mail in a specific time to remind me of stuffs
#   Last Change:    Function to send for telegram bot

"""
    TODO: Acrescentar opção no send para escolher entre enviar para email, telegram ou os dois
"""

import smtplib
import click
import os
import psycopg2
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from load_dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

passw = os.getenv("PASSWORD")
mail = os.getenv("EMAIL")
database = os.getenv("DATABASE")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_container = os.getenv("DB_CONTAINER")
db_host = os.getenv("HOST")
db_port = os.getenv("PORT")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not mail or not passw:
    print(f"> Variable MAIL or PASSW not found.")
    exit(1)

def connect_db(cur, conn):
    conn = psycopg2.connect(dbname=database, user=db_user, password=db_password, host=db_host, port=int(db_port))
    cur = conn.cursor()
    return cur, conn

def send_telegram_message(
    bot_token: str,
    chat_id: str,
    message: str,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: bool = False,
    disable_notification: bool = False,
    reply_to_message_id: Optional[int] = None
) -> Dict[str, Any]:
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": disable_web_page_preview,
        "disable_notification": disable_notification
    }
    
    # Add optional parameters
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if not result.get("ok"):
            raise ValueError(f"Telegram API error: {result.get('description', 'Unknown error')}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to send message: {e}")


@click.group()
def cli():
    """> Send Mail to remind off stuff."""
    pass

@cli.command(help="> List reminders.")
def list():
    try:
        cur, conn = connect_db(None, None)
        cur.execute("select Id, Message, TO_CHAR(Creation_Date, 'dd/mm') from public.reminder order by Message asc")
        rows = cur.fetchall()

        for i in rows:
            #print(f"> Id: {i[0]} | Message: {i[1]} | Date: {i[2]}")
            print(f"> Id: {i[0]} | Message: {i[1]}")
                
        conn.commit()

    except Exception as e:
        print(f"> An error occurred: {e}")

@cli.command(help="> Insert a new reminder")
@click.argument('message', type=str)
def insert(message):
    try:
        cur, conn = connect_db(None, None)
        message = message.strip()
        cur.execute("""
            insert into public.reminder (message)
            VALUES (%s);
            """,
            (message,))
        conn.commit()
        print(f"> Reminder > {message} < inserted.")
                
    except Exception as e:
        print(f"> An error occurred: {e}")

@cli.command(help="Delete an item reminders.")
@click.argument('id', type=int)
def delete(id):
    try:
        cur, conn = connect_db(None, None)
        
        # Verifica se o registro existe antes de deletar
        cur.execute("SELECT Id FROM public.reminder WHERE Id = %s;", (id,))
        if cur.fetchone():
            cur.execute("DELETE FROM public.reminder WHERE Id = %s;", (id,))
            conn.commit()
            print(f"> Reminder > {id} < deleted.")
        else:
            print(f"> Reminder {id} not found.")

    except Exception as e:
        print(f"> An error occurred: {e}")
    finally:
        # Fechar conexão com o banco de dados
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@cli.command(help="> Delete all reminders.")
def clear():
    try:
        cur, conn = connect_db(None, None)
        cur.execute("""
            DELETE FROM public.reminder;
            """,
            )
        conn.commit()
        print(f"> Table cleared.")

    except Exception as e:
        print(f"> An error occurred: {e}")

@cli.command(help="> Send Mail.")
def send():
    def list_reminders():
        try:
            cur, conn = connect_db(None, None)
            cur.execute("SELECT Message, TO_CHAR(Creation_Date, 'dd/mm/YYYY') FROM public.reminder ORDER BY Message ASC")
            reminders = cur.fetchall()
            conn.commit()
            return reminders
        except Exception as e:
            print(f"> Error listing reminders: {e}")
            return []
        
    # -> Mail
    #try:
    #    
    #    reminders = list_reminders()
    #    if not reminders:
    #        print("> There is no reminders to send.")
    #        return
    #    
    #    message = MIMEMultipart()
    #    message['Subject'] = "### LEMBRETES ###"
    #    message['From'] = mail
    #    message['To'] = mail
    #    body = "\n".join([f"> {r[0]}" for r in reminders])
    #    #body = "\n".join([f"> {r[0]}" for r in reminders])
    #    message.attach(MIMEText(body, 'plain'))
    #    s = smtplib.SMTP('smtp.gmail.com', 587)
    #    s.starttls()
    #    s.login(mail, passw)
    #    s.send_message(message)
    #    print(f"> SUCCESS - Mail")
    #except Exception as e:
    #    print(f"> Error: {str(e)}.")
    
    # -> Telegram
    try:
        reminders = list_reminders()
        if reminders:
            markdown_message = "📋 *LEMBRETES DO DIA*\n"
            markdown_message += "═" * 25 + "\n"
            for i, reminder in enumerate(reminders, 1):
                #markdown_message += f"🔹 *{i}.* {reminder[0]}\n\n"
                markdown_message += f"🔹{reminder[0]}\n"
            markdown_message += "─" * 25 + "\n"
        else:
            markdown_message = "✅ *Nenhum lembrete para hoje!*\n\n🎉 Você está em dia!"

        result = send_telegram_message(
            bot_token=BOT_TOKEN,
            chat_id=CHAT_ID,
            message=markdown_message,
            parse_mode="Markdown"
        )
        print("> SUCCESS - Telegram")
    
    except Exception as e:
        print(f"> Error: {str(e)}")

    finally:
        if 's' in locals():
            s.quit()

if __name__ == "__main__":
    cli(prog_name='main')