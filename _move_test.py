import os, io, django, random, shutil
os.environ.setdefault("DJANGO_SETTINGS_MODULE","core.settings")
django.setup()
import logging; logging.disable(logging.CRITICAL)
from unittest import mock
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import move as _move
from PIL import Image
from apps.products.models import Product

# Emulate Linux: a spooled temp upload is *moved* to its destination, so the
# source path no longer exists afterwards. Second use of the same temp -> ENOENT.
moved=set()
def linux_like_move(old, new, chunk_size=65536, allow_overwrite=False):
    if old in moved: raise FileNotFoundError(2, "No such file or directory", old)
    shutil.copyfile(old, new); moved.add(old)
big=Image.frombytes("RGB",(2200,1500),bytes(random.getrandbits(8) for _ in range(2200*1500*3)))
b=io.BytesIO(); big.save(b,"PNG"); data=b.getvalue(); print("png MB", round(len(data)/1e6,1))
c=Client(HTTP_HOST="localhost", raise_request_exception=False)
def up(): return SimpleUploadedFile("camera1.png",data,content_type="image/png")
base={"name":"n","category":"figure","regularPrice":"৳1","discountedPrice":"৳1","price":"৳1","stock":"1"}
with mock.patch("django.core.files.storage.filesystem.file_move_safe", linux_like_move):
    r=c.post("/api/products/",{**base,"id":"mv-a","slug":"mv-a","image":up(),"image_file":up()})
    print("create:", r.status_code, r.content[:120])
    if r.status_code==201:
        p=Product.objects.get(id="mv-a"); print("  image:",p.image.name,"| image_file:",p.image_file.name)
        r2=c.patch("/api/products/mv-a/",{"name":"n2","image":up(),"image_file":up()},content_type=None) if False else None
Product.objects.filter(id__startswith="mv-").delete()
