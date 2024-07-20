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

CURRENT_PROGRESS = 0
TITLE = ""
VOLUME_PATTERN = re.compile(".*(vol|v|vo|volume)\\d+.*\\.cbz", re.IGNORECASE)
CHAPTER_PATTERN = re.compile("Vol. [1-9][0-9]* Ch. [1-9][0-9]*", re.IGNORECASE)
PAGE_PATTERN = re.compile(".+(.jpeg|.jpg|.png)", re.IGNORECASE)
CBZ_PATTERN = re.compile(".+\\.cbz", re.IGNORECASE)


def start_progress(title):
    global CURRENT_PROGRESS
    sys.stdout.write(title + " [" + "-" * 40 + "]" + chr(8) * 41)
    sys.stdout.flush()
    CURRENT_PROGRESS = 0


def increment_progress(x):
    global CURRENT_PROGRESS
    x = int(x * 40 // 100)
    sys.stdout.write("#" * (x - CURRENT_PROGRESS))
    sys.stdout.flush()
    CURRENT_PROGRESS = x


def end_progress():
    sys.stdout.write("#" * (40 - CURRENT_PROGRESS) + "]\n")
    sys.stdout.flush()


def build_chapters(base_directory, volume, volume_path):
    """
    Builds chapters within a volume's directory into the relevant Vol. n Ch. m.cbz files.
    """
    prepare_loose_chapters(volume, volume_path)

    chapters = [
        path for path in os.listdir(volume_path) if re.match(CHAPTER_PATTERN, path)
    ]
    for chapter in chapters:
        chapter_path = f"{volume_path}/{chapter}"
        print(f"[COMPRESSING] {chapter}")
        shutil.make_archive(chapter_path, "zip", chapter_path)
        shutil.move(f"{chapter_path}.zip", f"{base_directory}/_output/{chapter}.cbz")
    print(f"[CLEANING UP] Deleting {volume_path}")
    shutil.rmtree(volume_path)


def prepare_loose_chapters(volume, volume_path):
    """
    Takes all loose pages in an unprepared volume directory and moves them to the appropriate Vol. n Ch. m folder where
    n is the volume number and m is the chapter number. Renames pages to page number format nnn.extn or nnn-nnn.extn.
    """

    pages = [path for path in os.listdir(volume_path) if re.match(PAGE_PATTERN, path)]

    start_progress(f"[BUILDING] {volume_path[volume_path.rfind(TITLE):]}")
    for i, page in enumerate(pages):
        chapter = re.search(r"c[0-9]{3}", page)
        chapter = int(chapter.group(0)[1:])
        chapter_path = f"{volume_path}/Vol. {volume} Ch. {chapter}"

        match = re.search(r"p[0-9]{3}-p[0-9]{3}", page) or re.search(
            r"p[0-9]{3}", page
        )
        page_name = f"{match.group(0).replace('p', '')}{page[page.rfind('.'):]}"
        if match is None:
            raise Exception(
                "You have an invalid file name in your path, please fix it first."
            )
        os.makedirs(os.path.dirname(f"{chapter_path}/{page_name}"), exist_ok=True)
        shutil.move(f"{volume_path}/{page}", f"{chapter_path}/{page_name}")
        increment_progress(int(i / len(pages) * 100))
    end_progress()


def main():
    global TITLE
    base_directory = os.getcwd()
    # shutil.rmtree(f"{base_directory}/_output")
    # os.remove(f"{base_directory}/.tmp.zip")
    TITLE = base_directory[base_directory.rfind("/") + 1 :]
    if len(sys.argv) > 2:
        base_directory = sys.argv[1]
    os.mkdir(f"{base_directory}/_output")

    # volume_paths in this case refers to the original volume.cbz files
    volume_paths = [path for path in os.listdir(base_directory) if re.match(VOLUME_PATTERN, path)]
    volumeless_chapter_paths = [path for path in os.listdir(base_directory) if not re.match(VOLUME_PATTERN, path)]
    volumeless_chapter_paths = list(filter(lambda x: re.match(CBZ_PATTERN, x), volumeless_chapter_paths))

    start_progress(f"[RENAMING] Renaming loose chapters...")
    # Rename loose chapters that don't have a volume yet.
    for i, chapter in enumerate(volumeless_chapter_paths):
        chapter_number = re.search("[1-9]{1}\\d*", chapter)
        if chapter_number and chapter_number.group(0) is None:
            continue
        chapter_number = chapter_number.group(0)

        shutil.copy2(f"{base_directory}/{chapter}", f"{base_directory}/_output/Ch. {chapter_number}.cbz")
        increment_progress(int(i / len(volumeless_chapter_paths) * 100))
    end_progress()

    # Handles volumes that need to be extracted and separated into chapters.
    for volume_path in volume_paths:
        # We want to copy those to a tmp zip file (to leave originals intact) then extract and cleanup the unneeded volume.zip file.
        # Extracted loose files are just named with the number of the volume.
        shutil.copy(volume_path, ".tmp.zip")
        volume = re.search(r"v[0-9]{1,3}", volume_path[volume_path.rfind("/") + 1 :])
        volume = int(volume.group(0)[1:])

        print(f"[EXTRACTING] {TITLE}{volume_path[volume_path.rfind("/"):]}")
        with ZipFile(f"{base_directory}/.tmp.zip", "r") as zObject:
            zObject.extractall(path=f"{base_directory}/.{volume}")

        os.remove(".tmp.zip")

        # Note that volume_path in this case refers to the *original* volume path, not the extracted one. We have to use the extracted one
        # for the build.
        build_chapters(base_directory, volume, f"{base_directory}/.{volume}")


if __name__ == "__main__":
    main()
