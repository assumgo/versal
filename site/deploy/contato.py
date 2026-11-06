#!/usr/bin/env python3
"""Receive the Versal Agro contact form and mail it to the commercial inbox."""

import json
import os
import re
import smtplib
import sys
import time
from collections import deque
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RECIPIENT = os.environ.get("CONTACT_TO", "comercial@versalagro.com.br")
SENDER = os.environ.get(
    "CONTACT_FROM",
    "Versal Agro <site@UbuntuVersal.tempe.ioflood.net>",
)
SMTP_HOST = os.environ.get("CONTACT_SMTP_HOST", "127.0.0.1")
SMTP_PORT = int(os.environ.get("CONTACT_SMTP_PORT", "25"))
LISTEN_HOST = os.environ.get("CONTACT_LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("CONTACT_LISTEN_PORT", "8092"))
MAX_BODY = 8_000
MAX_PER_WINDOW = 8
WINDOW_SECONDS = 600

COMPANY_RE = re.compile(r"^(?=.*[\w])[\w .&'-]{1,120}$", re.UNICODE)
EMAIL_RE = re.compile(r"^[^@\s]{1,80}@[^@\s]{1,80}\.[A-Za-z]{2,15}$")
HITS = {}


class ContactError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def single_line(value, limit):
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    return text[:limit].strip()


def field_text(form, key, limit):
    raw = form.get(key, "")
    if isinstance(raw, dict):
        raw = raw.get("value", "")
    return single_line(raw, limit)


def parse_contact(payload):
    if not isinstance(payload, dict):
        raise ContactError(400, "Dados inválidos.")
    form = payload.get("formData")
    if not isinstance(form, dict):
        raise ContactError(400, "Dados inválidos.")
    company = field_text(form, "Email", 120)
    visitor = field_text(form, "E-mail", 200)
    if not COMPANY_RE.fullmatch(company):
        raise ContactError(400, "Informe o nome da empresa.")
    reply_to = visitor if EMAIL_RE.fullmatch(visitor) else ""
    return company, visitor or "não informado", reply_to


def allow(ip):
    now = time.monotonic()
    recent = HITS.setdefault(ip, deque())
    while recent and now - recent[0] > WINDOW_SECONDS:
        recent.popleft()
    if len(recent) >= MAX_PER_WINDOW:
        return False
    recent.append(now)
    return True


def build_message(company, visitor, reply_to):
    message = EmailMessage()
    message["Subject"] = f"Contato pelo site — {company}"
    message["From"] = SENDER
    message["To"] = RECIPIENT
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(
        "\n".join(
            [
                "Mensagem enviada pelo formulário do site Versal Agro.",
                "",
                f"Nome da empresa: {company}",
                f"E-mail: {visitor}",
            ]
        )
    )
    return message


def deliver(message):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
        smtp.send_message(message)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        if self.path.split("?", 1)[0].rstrip("/") != "/contato":
            self.respond(404, {"ok": False, "error": "Não encontrado."})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > MAX_BODY:
            self.respond(400, {"ok": False, "error": "Dados inválidos."})
            return
        ip = single_line(self.headers.get("X-Real-IP", self.client_address[0]), 80)
        if not allow(ip or "local"):
            self.respond(429, {"ok": False, "error": "Muitas mensagens. Tente de novo em alguns minutos."})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            company, visitor, reply_to = parse_contact(payload)
            deliver(build_message(company, visitor, reply_to))
        except ContactError as error:
            self.respond(error.status, {"ok": False, "error": str(error)})
            return
        except (json.JSONDecodeError, UnicodeDecodeError, smtplib.SMTPException, OSError):
            self.respond(502, {"ok": False, "error": "Não foi possível enviar a mensagem."})
            return
        self.respond(200, {"ok": True})

    def respond(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


def check():
    company, visitor, reply_to = parse_contact(
        {
            "formData": {
                "Email": {"value": "Empresa 123", "type": "text"},
                "E-mail": {"value": "pessoa@exemplo.com", "type": "text"},
            }
        }
    )
    assert company == "Empresa 123"
    assert reply_to == "pessoa@exemplo.com"
    message = build_message(company, visitor, reply_to)
    assert message["To"] == RECIPIENT
    assert "Empresa 123" in message.get_content()
    try:
        parse_contact({"formData": {"Email": "a@b.com", "E-mail": ""}})
    except ContactError:
        pass
    else:
        raise SystemExit("company address was accepted")
    print("ok")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check()
        return
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    print(f"listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
