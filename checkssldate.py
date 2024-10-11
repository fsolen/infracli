import ssl
import socket
import datetime
import urllib.parse
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

def get_ssl_info(hostname, port=443):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
            der_cert = secure_sock.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(der_cert, default_backend())
            return cert

def is_self_signed(cert):
    return cert.issuer == cert.subject

def get_signature_algorithm_name(cert):
    return cert.signature_algorithm_oid._name

def get_certificate_hash(cert):
    return cert.fingerprint(hashes.SHA256()).hex()

def check_ssl_certificate(url):
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc
    if ':' in hostname:
        hostname, port = hostname.split(':')
        port = int(port)
    else:
        port = 443

    try:
        cert = get_ssl_info(hostname, port)
        expiry_date = cert.not_valid_after
        remaining_days = (expiry_date - datetime.datetime.now(expiry_date.tzinfo)).days
        self_signed = is_self_signed(cert)
        signature_algorithm = get_signature_algorithm_name(cert)
        cert_hash = get_certificate_hash(cert)

        print(f"Website: {url}")
        print(f"SSL Certificate Expiration Date: {expiry_date}")
        print(f"Remaining Days: {remaining_days}")
        print(f"Self-Signed: {'Yes' if self_signed else 'No'}")
        print(f"Issuer: {cert.issuer.rfc4514_string()}")
        print(f"Subject: {cert.subject.rfc4514_string()}")
        print(f"Version: {cert.version}")
        print(f"Serial Number: {cert.serial_number}")
        print(f"Signature Algorithm: {signature_algorithm}")
        print(f"Certificate Hash (SHA256): {cert_hash}")
        
    except Exception as e:
        print(f"Error checking SSL certificate for {url}: {str(e)}")

if __name__ == "__main__":
    url_to_check = "https://fatihsolen.com"
    check_ssl_certificate(url_to_check)
