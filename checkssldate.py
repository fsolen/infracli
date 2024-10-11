import ssl
import socket
import datetime
import urllib.parse
from cryptography import x509
from cryptography.hazmat.backends import default_backend

def get_ssl_expiry(hostname, port=443):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
            der_cert = secure_sock.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(der_cert, default_backend())
            return cert.not_valid_after

def check_ssl_certificate(url):
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc
    if ':' in hostname:
        hostname, port = hostname.split(':')
        port = int(port)
    else:
        port = 443

    try:
        expiry_date = get_ssl_expiry(hostname, port)
        remaining_days = (expiry_date - datetime.datetime.now(expiry_date.tzinfo)).days

        print(f"Website: {url}")
        print(f"SSL Certificate Expiration Date: {expiry_date}")
        print(f"Remaining Days: {remaining_days}")
    except Exception as e:
        print(f"Error checking SSL certificate for {url}: {str(e)}")

if __name__ == "__main__":
    url_to_check = "https://fatihsolen.com"
    check_ssl_certificate(url_to_check)
