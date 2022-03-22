#!/usr/bin/env python
# -*- coding: utf-8 -*-
import mimetypes
import smtplib
import typing
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from urllib.parse import urlparse

import socks


class EmailUtil(object):
    def __init__(self, host: str, port: int, passwd: str, from_addr: str,
                 tls: bool = True, proxy_url: str = None, debug: bool = True,
                 proxy_auth: typing.Optional[typing.Tuple] = None):

        self.smtp_host = host
        self.smtp_port = port
        self.from_addr = from_addr
        self.password = passwd
        self.tls = tls
        self.encoding = 'utf-8'

        self.from_name = ""
        self.to_name = ""

        if proxy_url:
            self.proxy = proxy_url
            self.proxy_auth = proxy_auth
            smtplib.SMTP._get_socket = self._smtplib_get_socket
        self.debug_level = 1 if debug else 0

    def _smtplib_get_socket(self, host, port, timeout):
        proxy_url = urlparse(self.proxy)
        # Patched SMTP._get_socket
        return socks.create_connection(
            (host, port),
            timeout,
            proxy_type=socks.PROXY_TYPES[proxy_url.scheme.upper()],
            proxy_addr=proxy_url.hostname,
            proxy_port=proxy_url.port,
            proxy_username=self.proxy_auth[0] if self.proxy_auth else None,
            proxy_password=self.proxy_auth[1] if self.proxy_auth else None,
        )

    def _format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr((self._encode(name), addr))

    def _send_email(self, msg):
        if self.smtp_port == 465:
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        elif self.smtp_port in (587, 25):
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.tls:
                server.starttls()
        else:
            raise Exception('port {} not support'.format(self.smtp_port))
        server.set_debuglevel(self.debug_level)
        server.login(self.from_addr, self.password)
        server.sendmail(self.from_addr, self.to_addr, msg.as_string())
        server.quit()

    def _encode(self, msg):
        return Header(msg, self.encoding).encode()

    def _get_msg(self, subject):
        msg = MIMEMultipart()
        msg['From'] = self._format_addr('%s <%s>' % (self.from_name, self.from_addr))
        msg['To'] = self._format_addr('%s <%s>' % (self.to_name, ','.join(self.to_addr)))
        msg['Subject'] = self._encode(subject)
        return msg

    def _get_content_type(self, name):
        content_type, encoding = mimetypes.guess_type(name, strict=False)
        content_type = content_type or "application/octet-stream"
        maintype, subtype = content_type.split("/")
        return maintype, subtype, encoding

    def _send_file(self, file_name, content=None):
        maintype, subtype, _ = self._get_content_type(file_name)
        # maintype, subtype = content_type.split("/")
        mime = MIMEBase(maintype, subtype, filename=self._encode(file_name))
        # 加上必要的头信息:
        mime.add_header('Content-Disposition', 'attachment', filename=self._encode(file_name))
        # 把附件的内容读进来:
        mime.set_payload(content)
        # 用Base64编码:
        encoders.encode_base64(mime)
        # 添加到MIMEMultipart:
        # msg.attach(mime)
        return mime

    def send_email(self, to_addr: typing.Union[typing.List, str], subject: str, text: str, msg_type='plain',
                   file_name=None, file_content=None):
        self.to_addr = to_addr
        # content = utf8(content) if content is not None else content
        if msg_type in ('plain', 'html'):
            self.msg_type = msg_type
        else:
            raise Exception("msg_type should is plain or html")

        msg = self._get_msg(subject)
        msg.attach(MIMEText(text, self.msg_type, self.encoding))
        if file_content is not None:
            msg.attach(self._send_file(file_name, file_content))
        self._send_email(msg)
