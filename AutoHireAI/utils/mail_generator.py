"""
This module has been deprecated. All email functionality has been moved to email_utils.py.
Please use the send_interview_invitation function from email_utils.py instead.
"""

from utils.email_utils import send_interview_invitation

# For backward compatibility
def send_email(*args, **kwargs):
    """Deprecated: Use email_utils.send_interview_invitation instead"""
    return send_interview_invitation(*args, **kwargs)