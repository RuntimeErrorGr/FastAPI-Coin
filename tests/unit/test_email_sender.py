from unittest.mock import patch

from app.services.email_sender import EmailSender


def test_send_delivers_a_plain_text_email():
    sender = EmailSender("smtp.test", 1025, sender="Coin API <noreply@test>")

    with patch("app.services.email_sender.smtplib.SMTP") as smtp_class:
        sender.send("bob@example.com", "Hello", "Body text")

    smtp_class.assert_called_once_with("smtp.test", 1025, timeout=10)
    smtp = smtp_class.return_value.__enter__.return_value
    smtp.starttls.assert_not_called()
    smtp.login.assert_not_called()
    message = smtp.send_message.call_args.args[0]
    assert (message["From"], message["To"], message["Subject"]) == (
        "Coin API <noreply@test>",
        "bob@example.com",
        "Hello",
    )
    assert message.get_content().strip() == "Body text"


def test_send_uses_tls_and_login_when_configured():
    sender = EmailSender(
        "smtp.test", 587, sender="x@test", username="user", password="pw", starttls=True
    )

    with patch("app.services.email_sender.smtplib.SMTP") as smtp_class:
        sender.send("bob@example.com", "Hello", "Body text")

    smtp = smtp_class.return_value.__enter__.return_value
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("user", "pw")
