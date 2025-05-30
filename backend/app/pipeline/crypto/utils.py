from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

def encrypt_with_public_key(public_key_pem: str, plaintext: str) -> bytes:
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    encrypted = public_key.encrypt(
        plaintext.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return encrypted

def decrypt_with_private_key(private_key_pem: str, encrypted_data: bytes) -> str:
    private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    decrypted = private_key.decrypt(
        encrypted_data,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return decrypted.decode()
