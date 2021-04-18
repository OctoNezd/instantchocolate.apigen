import json
import os
import time

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

MAP_SCHEME = {
    "packageName": "title",
    "displayName": "d:Title",
    "summary": "summary",
    "version": "d:Version",
    "icon": "d:IconUrl",
    "author": "author name",
    "downloadCount": "d:DownloadCount"
}
PACKAGEINFO_SCHEME = {
    "description": "d:Description",
    "updated": "updated",
    "galleryUrl": "d:GalleryDetailsUrl",
    "abuseUrl": "d:ReportAbuseUrl",
    "licenseUrl": "d:LicenseUrl",
    **MAP_SCHEME
}


def map_to_scheme(entry, scheme):
    json_entry = {}
    for item, selector in scheme.items():
        # yeah it fucking sucks
        if ":" not in selector:
            item_xml = entry.select(selector)[0]
        else:
            item_xml = entry.find(selector)
        value = item_xml.text
        if value.isdigit():
            value = int(value)
        json_entry[item] = value
    return json_entry


def main():
    packages_total = int(requests.get("https://community.chocolatey.org/api/v2/Packages/$count",
                                      params={"$filter": "IsLatestVersion",
                                              }).text)
    os.makedirs("public/package_info", exist_ok=True)
    packages = []
    for skipval in tqdm(range(0, packages_total, 40)):
        r = requests.get("https://community.chocolatey.org/api/v2/Packages",
                         params={
                             "$skip": skipval,
                             "$orderby": "DownloadCount desc",
                             "$filter": "IsLatestVersion",
                         })
        xml = BeautifulSoup(r.text, features="xml")
        for entry in xml.findAll("entry"):
            json_entry = map_to_scheme(entry, MAP_SCHEME)
            packages.append(json_entry)

            if not os.environ.get("DONT_WRITE_PACKAGE_DATA", '0') == '1':
                print("Writing package data for", entry['packageName'])
                with open(f"public/package_info/{json_entry['packageName']}.json", 'w') as f: json.dump(
                    map_to_scheme(entry, PACKAGEINFO_SCHEME), f)
        # time.sleep(0.5)  # We are the good guys, I think? And there is probably ratelimiting too
    with open("public/package_data.json", 'w') as f:
        json.dump({"timestamp": time.time(), "software": packages}, f)


if __name__ == '__main__':
    main()
