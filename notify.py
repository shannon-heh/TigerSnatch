# ----------------------------------------------------------------------
# notify.py
# Sends users emails or text messages about enrollment updates
# ----------------------------------------------------------------------

from database import Database
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from sys import stderr
from config import TS_EMAIL, TS_PASSWORD


class Notify:
    # initializes Notify, fetching all information about a given classid
    # to format and send an email to the first student on the waitlist
    # for that classid

    def __init__(self, classid, swap=False):
        db = Database()
        self._classid = classid
        try:
            self._coursename, self._sectionname = db.classid_to_classinfo(
                classid)
            self._netid = db.get_class_waitlist(classid)['waitlist'][0]
        except:
            raise Exception(f'waitlist for class {classid} does not exist')
        self._email = db.get_user(self._netid)['email']

        self._swap = swap
        if swap:
            self._netid_swap = ''
            self._sectionname_swap = ''

    # returns the primary (non-swap) netid of this Notify object

    def get_netid(self):
        return self._netid

    # sends a formatted email to the first person on waitlist of class with
    # self.classid

    def send_email_html(self):
        msg = EmailMessage()
        asparagus_cid = make_msgid()
        msg.add_alternative(f"""\
        <html>
        <head></head>
        <body>
            <p>Dear srijam,</p>
            <p>Your requested section <b>{self._sectionname}</b> in <b>{self._coursename}</b> has a spot open! You have been removed from the waitlist on TigerSnatch. The next student on the waitlist will receive a notification in 5 minutes.</p>
            <p>Please head over to <a href="https://phubprod.princeton.edu/psp/phubprod/?cmd=start">Tigerhub</a> to register for your course!</p>
            <p>Best,<br>Tigersnatch Team</p>
        </body>
        </html>
        """.format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')

        if self._swap:
            msg.add_alternative(f"""\
            <html>
            <head></head>
            <body>
                <p>Dear {self._netid},</p>
                <p>Your requested section <b>{self._sectionname}</b> in <b>{self._coursename}</b> have a spot open! You have been removed from the waitlist on TigerSnatch. The next student on the waitlist will receive a notification in 5 minutes.
                <p>The netid of your match is: {self._netid_swap}. Please contact them to arrange a section swap!</p>
                <p>Best,<br>Tigersnatch Team</p>
            </body>
            </html>
            """.format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')

        me = TS_EMAIL
        you = self._email  # receiver
        pwd = TS_PASSWORD  # see config.py

        msg['Subject'] = f'A spot opened in {self._sectionname} {self._coursename}'
        msg['From'] = me
        msg['To'] = you
        s = smtplib.SMTP('smtp.office365.com', 587)

        try:
            s.starttls()
            s.login(me, pwd)
            s.send_message(msg)
            s.quit()
            return True
        except Exception as e:
            print(e, file=stderr)
            return False

    def __str__(self):
        ret = 'Notify:\n'
        ret += f'\tNetID:\t\t{self._netid}\n'
        ret += f'\tEmail:\t\t{self._email}\n'
        ret += f'\tCourse:\t\t{self._coursename}\n'
        ret += f'\tSection:\t{self._sectionname}\n'
        ret += f'\tClassID:\t{self._classid}'

        if self._swap:
            ret += f'\n\tSwap with:\t{self._netid_swap}\n'
            ret += f'\tSwap section:\t{self._sectionname_swap}'

        return ret


if __name__ == '__main__':
    n = Notify('41283')
    n.send_email_html()
