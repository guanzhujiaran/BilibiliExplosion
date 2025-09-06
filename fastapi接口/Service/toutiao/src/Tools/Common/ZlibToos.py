import zlib

def strToBlob(input_str:str)->bytes:
    return zlib.compress(input_str.encode('utf-8'))

def BlobToStr(blob:bytes)->str:
    return zlib.decompress(blob).decode('utf-8')

if __name__ == '__main__':
    a='1234'
    b=strToBlob(a)
    print(b)
    c=BlobToStr(b)
    print(c)