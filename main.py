#! /usr/bin/env python3

#   Author:         Pablo Andrade
#   Created:        29/11/2024
#   Version:        0.0.8
#   Objective:      Program to send reminders in a specific time to remind me of stuffs
#   Last Change:    fix: changed psql for sqlite3, visual and filters.

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
# Database
from database import Session, init_db
from models import Reminder

load_dotenv()

init_db()

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

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

if not mail or not passw:
    print(f"Variable MAIL or PASSW not found.")
    exit(1)

def print_table(headers, rows):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    print("┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐")
    header_row = "│"
    for i, header in enumerate(headers):
        header_row += f" {Colors.BOLD}{header.ljust(col_widths[i])}{Colors.RESET} │"
    print(header_row)
    print("├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤")
    for row in rows:
        data_row = "│"
        for i, cell in enumerate(row):
            data_row += f" {str(cell).ljust(col_widths[i])} │"
        print(data_row)
    print("└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘")

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
    session = Session()
    try:
        tdy = datetime.now().strftime("%B %d, %Y   %H:%M:%S")
        rem = session.query(Reminder).order_by(Reminder.event_date.asc()).all()
        
        print(f"\n{Colors.WHITE}{tdy}{Colors.RESET}\n")
        
        if not rem:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Empty.\n")
            return
        
        headers = ["ID", "Date", "Message"]
        rows = []
        
        for reminder in rem:
            event_date = reminder.display_event_date() if hasattr(reminder, 'display_event_date') else (
                reminder.event_date.strftime("%d/%m/%Y") if reminder.event_date else "Sem data"
            )
            rows.append([
                str(reminder.id),
                event_date,
                reminder.message or ''
            ])
        print_table(headers, rows)
        
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")
    finally:
        session.close()

@cli.command('insert')
@click.argument('message', type=str)
@click.argument('event_date', required=False, default=None)
def insert(message, event_date):
    """Insert a new record.

    Usage:\n
        reminder insert "New Record."\n
        reminder insert "New Record" "Date"\n
        reminder i "New Record."
        reminder i "New Record" "Date"\n
    """
    
    session = Session()
    try:
        new_rem = Reminder(
            message=message,
            event_date=event_date if event_date is not None else None
        )
        session.add(new_rem)
        session.commit()
        print(f"\n{Colors.GREEN}{Colors.BOLD}{message} inserted.{Colors.RESET}")
    except Exception as e:
        session.rollback()
        print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")
    finally:
        session.close()


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
    session = Session()
    try:
        for id in ids:
            reminder = session.query(Reminder).filter_by(id=id).first()            
            if reminder:
                message = reminder.message or ''
                session.delete(reminder)
                print(f"\n{Colors.GREEN}{Colors.BOLD}{message} deleted.{Colors.RESET}")
            else:
                print(f"\nID {id} not found.")
        session.commit()
                
    except Exception as e:
        session.rollback()
        print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")
    finally:
        session.close()

@cli.command('clear')
def clear():
    """Delete all records.

    Usage:\n
        reminder clear\n
        reminder c
    """
    session = Session()
    try:
        count = session.query(Reminder).count()
        
        if count == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}Table is already empty.{Colors.RESET}")
        else:
            session.query(Reminder).delete()
            session.commit()
            print(f"\n{Colors.GREEN}{Colors.BOLD}Table cleared. {count} record(s) deleted.{Colors.RESET}")
            
    except Exception as e:
        session.rollback()
        print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")
    finally:
        session.close()

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
        print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")

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
        session = Session()
        try:
            reminders = session.query(Reminder).order_by(Reminder.id.asc()).all()
            return reminders
        except Exception as e:
            print(f"An error occurred: {e}")
            return []
        finally:
            session.close()
    
    def send_telegram():
        try:
            reminders = list_reminders()
            if reminders:
                markdown_message = "📋 *LEMBRETES DO DIA*\n"
                markdown_message += "═" * 25 + "\n"
                for i, reminder in enumerate(reminders, 1):
                    msg = reminder.message or ''
                    ev = reminder.event_date or ''
                    markdown_message += f"🔹 *{i}.* {ev} {msg}\n"
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
            print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")
        finally:
            if 's' in locals():
                s.quit()

    def send_mail():
        try:

            reminders = list_reminders()
            if not reminders:
                print("There is no reminders to send.")
                return

            tdy = datetime.now().strftime("%B %d, %Y")
            message = MIMEMultipart()
            message['Subject'] = f"Lembretes - {tdy}"
            message['From'] = mail
            message['To'] = mail
            body = "\n".join([f"• {r.message or 'No message'} {r.event_date or ''}" for r in reminders])
            message.attach(MIMEText(body, 'plain'))
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(mail, passw)
            s.send_message(message)
            print(f"SUCCESS - Mail")
        except Exception as e:
            print(f"{Colors.RED}✗{Colors.RESET} Error: {Colors.RED}{Colors.BOLD}{e}{Colors.RESET}")
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