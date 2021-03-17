# ----------------------------------------------------------------------
# notify.py
# Sends users emails or text messages about enrollment updates
# ----------------------------------------------------------------------

from database import Database
import smtplib
from email.message import EmailMessage


class Notify:
    def __init__(self, classid, swap=False):
        db = Database()
        self._classid = classid
        self.coursename, self.sectionname = db.classid_to_classinfo(classid)
        self.secitionname_swap = ''
        self.netid = 'zishuoz'
        self.netid_swap = ''

    # def text(self, swap=False):
    #     try:
    #         return 0

    #     return 0

    def send_email(self, swap=False):
        msg_content = f'Dear {self.netid}\n'
        msg = EmailMessage()
        if swap:
            msg_content += f'Someone in {self.secitionname_swap} of {coursename} would like to swap section with you! Their netid is {self.netid_swap}. Please contact them to make any arrangements!\n\n'
        else:
            msg_content += f'Your requested section <b>{self.sectionname}</b> in <b>{self.coursename}</b> have a spot open! You have been removed from the waitlist on TigerSnatch. The next student on the waitlist will receive a notification in 5 minutes.\n\n\
            Please head over to <a href="https://phubprod.princeton.edu/psp/phubprod/?cmd=start">Tigerhub</a> to register for your course!'

        msg_content += '\nBest,\nTigerSnatch Team'
        msg.set_content(msg_content)
        me = 'zishuoz@princeton.edu'
        you = '15zhangb1234@gmail.com'
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()


if __name__ == '__main__':
    n = Notify('41337')
    n.send_email()
