import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Union, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials from environment (Recommended)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "numan.n.patil@gmail.com")
APP_PASSWORD = os.getenv("APP_PASSWORD", "btus gbcs ksgf ixwd")

# Office location for in-person interviews
OFFICE_ADDRESS = "123 Tech Park, Innovation Street, Silicon Valley, CA 94025"

# Virtual meeting link template
VIRTUAL_MEETING_LINK = "https://zoom.us/j/{meeting_id}"

def get_mode_specific_instructions(mode: str, location: Optional[str] = None) -> Dict[str, str]:
    """Return instructions and location based on interview mode."""
    mode = mode.lower()
    if mode == 'virtual':
        meeting_link = location or VIRTUAL_MEETING_LINK.format(meeting_id="12345678")
        return {
            "instructions": (
                "For this virtual interview:\n"
                "- Please join the Zoom meeting using the link below\n"
                "- Join 5 minutes before the scheduled time\n"
                "- Ensure you have a stable internet connection\n"
                "- Test your camera and microphone beforehand\n"
                "- Find a quiet place for the interview"
            ),
            "location": meeting_link
        }
    elif mode == 'in-person':
        office_address = location or OFFICE_ADDRESS
        return {
            "instructions": (
                "For this in-person interview:\n"
                "- Please arrive 10 minutes before the scheduled time\n"
                "- Bring a copy of your resume\n"
                "- Please report to the reception upon arrival\n"
                "- Dress code: Business professional"
            ),
            "location": office_address
        }
    else:  # Phone
        return {
            "instructions": (
                "For this phone interview:\n"
                "- We will call you at the provided number\n"
                "- Please ensure you are in an area with good network coverage\n"
                "- Keep your phone charged and readily available\n"
                "- Have a pen and paper ready for notes"
            ),
            "location": "Phone Interview"
        }

def format_date(date_str: str) -> str:
    """Format date string to a readable format."""
    try:
        if not date_str:
            raise ValueError("Date is required")
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%A, %B %d, %Y')
    except ValueError as e:
        logger.warning(f"Invalid date format: {date_str}")
        raise ValueError(f"Invalid date format: {date_str}") from e

def send_interview_invitation(
    candidate_email: str,
    candidate_name: str,
    position: str,
    interview_date: str,
    interview_time: str,
    interview_mode: str,
    interview_location: Optional[str] = None
) -> Dict[str, Union[bool, Dict[str, str], str]]:
    """Send an interview invitation email to a candidate."""
    try:
        # Input validation
        if not all([candidate_email, candidate_name, position, interview_date, interview_time, interview_mode]):
            raise ValueError("Missing required fields for sending email")

        # Validate email format
        if not '@' in candidate_email or not '.' in candidate_email:
            raise ValueError(f"Invalid email format: {candidate_email}")

        # Format subject
        subject = f"Interview Invitation: {position} Position"

        # Format date
        formatted_date = format_date(interview_date)

        # Get mode-specific instructions and location
        mode_info = get_mode_specific_instructions(interview_mode, interview_location)
        instructions = mode_info['instructions']
        location = mode_info['location']

        # Create HTML body with improved styling
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #ffffff; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0;">Interview Invitation</h2>
                </div>
                
                <div style="padding: 20px;">
                    <p>Dear {candidate_name},</p>
                    
                    <p>We are pleased to invite you for an interview for the <strong>{position}</strong> position.</p>
                    
                    <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 0 5px 5px 0;">
                        <h3 style="margin-top: 0; color: #28a745;">Interview Details</h3>
                        <p><strong>📅 Date:</strong> {formatted_date}</p>
                        <p><strong>🕒 Time:</strong> {interview_time}</p>
                        <p><strong>🎯 Mode:</strong> {interview_mode}</p>
                        <p><strong>📍 Location:</strong> {location}</p>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #2c3e50;">Important Instructions</h3>
                        <div style="white-space: pre-line;">{instructions}</div>
                    </div>
                    
                    <p>Please confirm your attendance by replying to this email.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p>Best regards,<br>
                        Hiring Team</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Create plain text body
        text_body = (
            f"Interview Invitation: {position} Position\n\n"
            f"Dear {candidate_name},\n\n"
            f"We are pleased to invite you for an interview for the {position} position.\n\n"
            "Interview Details:\n"
            f"- Date: {formatted_date}\n"
            f"- Time: {interview_time}\n"
            f"- Mode: {interview_mode}\n"
            f"- Location: {location}\n\n"
            "Important Instructions:\n"
            f"{instructions}\n\n"
            "Please confirm your attendance by replying to this email.\n\n"
            "Best regards,\n"
            "Hiring Team"
        )

        # Create MIME message
        msg = MIMEMultipart('alternative')
        msg["From"] = f"Hiring Team <{SENDER_EMAIL}>"
        msg["To"] = candidate_email
        msg["Subject"] = subject

        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {candidate_email}")
        return {
            "success": True,
            "preview": {
                "to": candidate_email,
                "subject": subject,
                "body": text_body,
                "name": candidate_name,
                "position": position,
                "date": formatted_date,
                "time": interview_time,
                "mode": interview_mode,
                "location": location
            }
        }

    except ValueError as ve:
        error_msg = str(ve)
        logger.error(f"Validation error: {error_msg}")
        return {"success": False, "error": error_msg}

    except smtplib.SMTPException as se:
        error_msg = f"SMTP error: {str(se)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}