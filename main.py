import json as j
from sys import argv
import requests as r
from hashlib import md5
from os import listdir, rename
from os.path import exists

def hex_to_uuid(h):
    return h[:8] + "-" + h[8:12] + "-" + h[12:16] + "-" + h[16:20] + "-" + h[20:]

def gen_offline_uuid(name):
    bin_hash = list(md5(bytes("OfflinePlayer:" + name, encoding="utf-8")).digest())
    bin_hash[6] = bin_hash[6] & 0x0f | 0x30
    bin_hash[8] = bin_hash[8] & 0x3f | 0x80

    return hex_to_uuid(bytes(bin_hash).hex())

def maybe_file_pair(uuid):
    try:
        uuid_ = uuid.replace("-", "")
        resp = r.get("https://api.mojang.com/user/profile/" + uuid_).json()

        return [(uuid + ".json", gen_offline_uuid(resp["name"]) + ".json")]

    except Exception:
        return []

def migrate(old, new):
    old = j.load(open(old))
    new = j.load(open(new))
    res = {"DataVersion": new["DataVersion"]}
    del old["DataVersion"]
    del new["DataVersion"]

    for k in set(old.keys()) | set(new.keys()):
        may_old = old.get(k)
        may_old_criteria = may_old["criteria"] if may_old else dict()
        may_old_done = may_old["done"] if may_old else False

        may_new = new.get(k)
        may_new_criteria = may_new["criteria"] if may_new else dict()
        may_new_done = may_new["done"] if may_new else False

        # '|' seems to be right biased; prefer earlier dates of criteria.
        res[k] = {
            "criteria": may_new_criteria | may_old_criteria,
            "done": may_new_done or may_old_done
        }

    #--------------------------------------------------
    # comment this out if you just want to test things!
    j.dump(res, open(new, "w"), indent=2)
    #--------------------------------------------------


# remove ".json" from files in current dir
uuids = map(lambda s: s[:-5], listdir())

file_maps = sum(map(maybe_file_pair, uuids), start=[])

for (old, new) in file_maps:
    # if both exist, merge
    if exists(old) and exists(new):
        try:
            migrate(old, new)
        except Exception as e:
            print("couldn't migrate %s -> %s: %s" % (old, new, repr(e)))
            raise e
    # if only "old" exists, rename
    elif exists(old):
        rename(old, new)
