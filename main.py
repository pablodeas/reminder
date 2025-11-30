#! /usr/bin/env python3

#   Author:         Pablo Andrade
#   Created:        29/11/2024
#   Version:        0.0.8
#   Objective:      Program to send reminders in a specific time to remind me of stuffs
#   Last Change:    Added calendar, aliases and time.

"""
    TODO:
"""

import smtplib
import click
import os
import psycopg2
import requests
import calendar
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from load_dotenv import load_dotenv
from typing import Optional, Dict, Any
from datetime import datetime

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
    print(f"Variable MAIL or PASSW not found.")
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
    """Save reminders and send to Telegram, Mail or both."""
    pass

@cli.command('list')
def list():
    """List records.

    Usage:\n
        reminder list\n
        reminder l
    """
    try:
        tdy = datetime.now().strftime("%B %d, %Y   %H:%M:%S")
        cur, conn = connect_db(None, None)
        cur.execute("select Id, Message, TO_CHAR(Creation_Date, 'dd/mm') from public.reminder order by Id asc")
        rows = cur.fetchall()

        print()
        print(tdy)
        print()
        for i in rows:
            print(f"Id: {i[0]}   {i[1]}")
                
        conn.commit()

    except Exception as e:
        print(f"An error occurred: {e}")

@cli.command('insert')
@click.argument('message', type=str)
def insert(message):
    """Insert a new record.

    Usage:\n
        reminder insert "New Record."\n
        reminder i "New Record."
    """
    try:
        cur, conn = connect_db(None, None)
        message = message.strip()
        cur.execute("""
            insert into public.reminder (message)
            VALUES (%s);
            """,
            (message,))
        conn.commit()
        print(f"{message} inserted.")
                
    except Exception as e:
        print(f"An error occurred: {e}")

@cli.command('delete')
@click.argument('ids', nargs=-1, type=int)
def delete(ids):
    """Delete one or multiple records.

    Usage:\n
        reminder delete Id\n
        reminder delete 10\n
        reminder delete 10 11 12\n
        reminder d Id\n
        reminder d 10\n
        reminder d 10 11 12
    """
    try:
        cur, conn = connect_db(None, None)
        
        for id in ids:
            cur.execute("SELECT Id, Message FROM public.reminder WHERE Id = %s;", (id,))
            rows = cur.fetchall()
            for i in rows:
                click.echo(f"{i[1]} deleted.")
            if rows:
                cur.execute("DELETE FROM public.reminder WHERE Id = %s;", (id,))
                conn.commit()
            else:
                print(f"{id} not found.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Fechar conexão com o banco de dados
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@cli.command('clear')
def clear():
    """Delete all records.

    Usage:\n
        reminder clear\n
        reminder c
    """
    try:
        cur, conn = connect_db(None, None)
        cur.execute("""
            DELETE FROM public.reminder;
            """,
            )
        conn.commit()
        print(f"Table cleared.")

    except Exception as e:
        print(f"An error occurred: {e}")

@cli.command('calendar')
@click.argument('month', type=int, required=False)
@click.argument('year', type=int, required=False)
def show_calendar(month, year):
    """Show calendar for current or specified month.
    
    Usage:\n
        reminder calendar\n
        reminder calendar 12 2024\n
        reminder cal\n
        reminder cal 12 2024\n
    """
    try:
        now = datetime.now()
        month = month or now.month
        year = year or now.year

        cal = calendar.month(year, month)
        click.echo(now.strftime("\n%B %d, %Y   %H:%M:%S\n"))
        click.echo(cal)

    except Exception as e:
        print(f"An error occurred: {e}")

@cli.command('send')
@click.argument('type', type=str, default='')
def send(type):
    """Send records to Telegram group, Mail or both.
    
    Usage:\n
        reminder send telegram  # Send only to Telegram\n
        reminder send mail      # Send only to Mail\n
        reminder send           # Send to both\n
        reminder s telegram     # Send only to Telegram\n
        reminder s mail         # Send only to Mail\n
        reminder s              # Send to both
    """
    def list_reminders():
        try:
            cur, conn = connect_db(None, None)
            cur.execute("SELECT Message, TO_CHAR(Creation_Date, 'dd/mm/YYYY') FROM public.reminder ORDER BY Message ASC")
            reminders = cur.fetchall()
            conn.commit()
            return reminders
        except Exception as e:
            print(f"Error listing reminders: {e}")
            return []
    
    def send_telegram():
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
            print("SUCCESS - Telegram")
    
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            if 's' in locals():
                s.quit()

    def send_mail():
        try:

            reminders = list_reminders()
            if not reminders:
                print("There is no reminders to send.")
                return

            message = MIMEMultipart()
            message['Subject'] = "### LEMBRETES ###"
            message['From'] = mail
            message['To'] = mail
            body = "\n".join([f"{r[0]}" for r in reminders])
            message.attach(MIMEText(body, 'plain'))
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(mail, passw)
            s.send_message(message)
            print(f"SUCCESS - Mail")
        except Exception as e:
            print(f"Error: {str(e)}.")
        finally:
            if 's' in locals():
                s.quit()

    if type == 'mail' or type == 'Mail' or type == 'MAIL':
        send_mail()
    
    if type == 'telegram' or type == 'Telegram' or type == 'TELEGRAM':
        send_telegram()

    if type == '':
        send_mail()
        send_telegram()

if __name__ == "__main__":
    cli.add_command(list, name='l')
    cli.add_command(insert, name='i')
    cli.add_command(delete, name='d')
    cli.add_command(clear, name='c')
    cli.add_command(send, name='s')
    cli.add_command(show_calendar, name='cal')
    cli(prog_name='main')