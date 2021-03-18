# ----------------------------------------------------------------------
# notify.py
# Sends users emails or text messages about enrollment updates
# ----------------------------------------------------------------------

from database import Database
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid


class Notify:
    def __init__(self, classid, swap=False):
        db = Database()
        self._classid = classid
        self.coursename, self.sectionname = db.classid_to_classinfo(classid)
        try:
            self.netid = db.get_class_waitlist(classid)[0]
        except:
            raise Exception(f'waitlist for class {classid} does not exist')
        self.email = db.get_user(self.netid)['email']
        self.netid_swap = ''
        self.secitionname_swap = ''

    # sends a formatted email to the first person on waitlist of class with
    # self.classid
    def send_email_html(self, swap=False):
        msg = EmailMessage()
        asparagus_cid = make_msgid()
        msg.add_alternative(f"""\
        <html>
        <head></head>
        <body>
            <p>Dear {self.netid},</p>
            <p>Your requested section <b>{self.sectionname}</b> in <b>{self.coursename}</b> has a spot open! You have been removed from the waitlist on TigerSnatch. The next student on the waitlist will receive a notification in 5 minutes.</p>
            <p>Please head over to <a href="https://phubprod.princeton.edu/psp/phubprod/?cmd=start">Tigerhub</a> to register for your course!</p>
            <p>Best,<br>Tigersnatch Team &#128047</p>
        </body>
        </html>
        """.format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')

        if swap:
            msg.add_alternative(f"""\
            <html>
            <head></head>
            <body>
                <p>Dear {self.netid},</p>
                <p>Your requested section <b>{self.sectionname}</b> in <b>{self.coursename}</b> have a spot open! You have been removed from the waitlist on TigerSnatch. The next student on the waitlist will receive a notification in 5 minutes.
                <p>The netid of your match is: {self.netid_swap}. Please contact them to arrange a section swap!</p>
                <p>Best,<br>Tigersnatch Team &#128047</p>
            </body>
            </html>
            """.format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')

        me = 'tigersnatch@princeton.edu'  # sender
        you = self.email  # receiver
        pwd = 'tigersnatch2021'  # sender's email

        msg['Subject'] = f'A spot opened in {self.sectionname} {self.coursename}'
        msg['From'] = me
        msg['To'] = you
        s = smtplib.SMTP('smtp.gmail.com', 587)

        try:
            s.starttls()
            s.login(me, pwd)
            s.send_message(msg)
            s.quit()
        except Exception as e:
            raise e


if __name__ == '__main__':
    n = Notify('41829')
    n.send_email_html()
