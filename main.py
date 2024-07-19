"""
Takes a set of CBZ files stored in volume format and converts them to a set of CBZ files in Vol. n Ch. m format where
"n" is the Volume number and "m" is the chapter number.
"""

import glob
import os
import re
import sys
import shutil
from zipfile import ZipFile

progress_x = 0
title = "MISSING TITLE"


def start_progress(title):
    global progress_x
    sys.stdout.write(title + " [" + "-" * 40 + "]" + chr(8) * 41)
    sys.stdout.flush()
    progress_x = 0


def progress(x):
    global progress_x
    x = int(x * 40 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x


def end_progress():
    sys.stdout.write("#" * (40 - progress_x) + "]\n")
    sys.stdout.flush()


def build_chapters(base_directory, volume, volume_path):
    """
    Creates the relevant loose folder directories for all Vol. n Ch. m entries in a volume format loose folder where "n"
    is the volume number and "m" is the chapter number. These are then used to rename and rebuild cbzs in Vol. n Ch. m
    format.
    """
    chapter_pattern = re.compile("Vol. [1-9][0-9]* Ch. [1-9][0-9]*")

    prepare_loose_chapters(volume, volume_path)

    chapters = [
        path for path in os.listdir(volume_path) if re.match(chapter_pattern, path)
    ]
    for chapter in chapters:
        chapter_path = f"{volume_path}/{chapter}"
        print(f"[COMPRESSING] {chapter}")
        shutil.make_archive(chapter_path, "zip", chapter_path)
        shutil.move(f"{chapter_path}.zip", f"{base_directory}/{chapter}.cbz")
    print(f"[CLEANING UP] Deleting {volume_path}")
    shutil.rmtree(volume_path)


def prepare_loose_chapters(volume, volume_path):
    """
    Takes all loose pages in an unprepared volume directory and moves them to the appropriate Vol. n Ch. m folder where
    n is the volume number and m is the chapter number. Renames pages to page number format nnn.extn or nnn-nnn.extn.
    """
    pages = glob.glob(f"{volume_path}/*.png")
    pages += glob.glob(f"{volume_path}/*.jpg")
    pages += glob.glob(f"{volume_path}/*.jpeg")

    start_progress(f"[BUILDING] {volume_path[volume_path.rfind(title):]}")
    for i in range(0, len(pages)):
        chapter = re.search(r"c[0-9]{3}", pages[i])
        chapter = int(chapter.group(0)[1:])
        chapter_path = f"{volume_path}/Vol. {volume} Ch. {chapter}"

        match = re.search(r"p[0-9]{3}-p[0-9]{3}", pages[i]) or re.search(
            r"p[0-9]{3}", pages[i]
        )
        page_name = f"{match.group(0).replace('p', '')}{pages[i][pages[i].rfind('.'):]}"
        if match is None:
            raise Exception(
                "You have an invalid file name in your path, please fix it first."
            )
        os.makedirs(os.path.dirname(f"{chapter_path}/{page_name}"), exist_ok=True)
        shutil.move(pages[i], chapter_path + f"/{page_name}")
        progress(int(i / len(pages) * 100))
    end_progress()


def main():
    global title
    base_directory = os.getcwd()
    title = base_directory[base_directory.rfind("/") + 1 :]
    if len(sys.argv) > 2:
        base_directory = sys.argv[1]

    # volume_paths in this case refers to the original volume.cbz files
    volume_paths = glob.glob(f"{base_directory}/*.cbz")
    for volume_path in volume_paths:
        if volume_path.rfind(".cbz") == -1:
            continue

        # We want to copy those to a tmp zip file (to leave originals intact) then extract and cleanup the unneeded volume.zip file.
        # Extracted loose files are just named with the number of the volume.
        shutil.copy(volume_path, "tmp.zip")
        volume = re.search(r"v[0-9]{1,3}", volume_path[volume_path.rfind("/") + 1 :])
        volume = int(volume.group(0)[1:])

        print(f"[EXTRACTING] {title}{volume_path[volume_path.rfind("/"):]}")
        with ZipFile(f"{base_directory}/tmp.zip", "r") as zObject:
            zObject.extractall(path=f"{base_directory}/{volume}")

        os.remove("tmp.zip")

        # Note that volume_path in this case refers to the *original* volume path, not the extracted one. We have to use the extracted one
        # for the build.
        build_chapters(base_directory, volume, f"{base_directory}/{volume}")


if __name__ == "__main__":
    main()
