import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 密钥和 IV（注意必须为 16 字节）
KEY = b'tencent_smmember'  # 16 bytes
IV = b'tencent_memberiv'  # 16 bytes


def decrypt_string(encrypted_string):
    """
    解码它里面有的一些加密了的字符串
    :param encrypted_string:
    :return:
    """
    # Base64 解码
    ciphertext = base64.b64decode(encrypted_string)

    # 创建 AES CBC 解密器
    cipher = AES.new(KEY, AES.MODE_CBC, IV)

    # 解密并去除填充
    decrypted = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted, AES.block_size).decode('utf-8')

    return plaintext


if __name__ == '__main__':
    print(decrypt_string(
        "+Qf/sH3IDByTecAa+hzVpZF4xHGB3CR/34HNQgcfi7GCJ7vvhymABE/osIFvWVgXCKo6RP/7AeT84inVI+lucR2AtqCABEJGXWKNCK1bQoMKvhr+TGxWiP5pDxxTLZASDgjusrqjdUv1xIk4l9/AgCgxbt6krfl20xGumcpbtXaXOZ3WBRWxuj0+2hFvRcMSgDi8MK7LdDHy5o9npoTnSb3yCqyagCANJNKwsFQkUpWAbKfWUQlMC7JHg/4gsM0GMGvvV9RNNdwi+cm4X1zYqehKxFj7RJkiPqpCf2vEt2zPhr4dSKIJMpGCbFrhEDDqLL8SsD5jeaQUtVJTTMTGtbHXTCiJ6GFXcJBYbqwcy0D2bz/Hf2XqcI/2/XZfH3gLbkHK/3t3Om91HyzgKCcnOcbl7L9Nfg=="
    )

    )
