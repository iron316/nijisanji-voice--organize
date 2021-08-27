import argparse
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import yaml


def extract_zipfile(zip_path: Path, out_dir: Path) -> Path:
    out_path = out_dir / str(zip_path).split("/")[-1].replace(".zip", "")
    out_path.mkdir(exist_ok=True, parents=True)
    with zipfile.ZipFile(str(zip_path)) as f:
        for info in f.infolist():
            try:
                info.filename = info.filename.encode("cp437").decode("cp932")
            except:
                pass
            f.extract(info, str(out_path))
    return out_path


def extract_file_info(dir_name: str, liver_info_path: str) -> Tuple[str, str, bool]:
    if dir_name.count("_") > dir_name.count(" "):
        sep = "_"
    else:
        sep = " "
    voice_category = dir_name.split(sep)[-1]
    liver_info_df = pd.read_csv(liver_info_path)
    liver_name = "unkown"
    for name in liver_info_df["name"]:
        if name in dir_name or name in dir_name.replace("_", "・"):
            liver_name = name
    return liver_name, voice_category, "EX" in dir_name


def extract_liver_names(dir_name: str, liver_info_path: str) -> str:
    liver_info_df = pd.read_csv(liver_info_path)
    names = []
    for name in liver_info_df["name"]:
        if name in dir_name or name in dir_name.replace("_", "・"):
            names.append(name)
    return "(" + "&".join(names) + ")"


def organize_image(extracted_path: Path, config: Dict[str, str]) -> None:
    zip_file = list(extracted_path.glob("ボイス/*"))[0]
    file_name = str(zip_file).split("/")[-1].replace(".zip", "").replace(".mp3", "")
    liver_names = extract_liver_names(extracted_path.name, config["liver_info_path"])
    _, voice_category, _ = extract_file_info(file_name, config["liver_info_path"])
    target_dir = Path(config["image_target_path"]) / (voice_category + liver_names)
    target_dir.mkdir(exist_ok=True, parents=True)
    for p in extracted_path.glob("特典壁紙/*"):
        file_name = p.name
        shutil.copy(str(p), str(target_dir / file_name))


def organize_voice(source_path: Path, config: Dict[str, str]) -> None:
    tmp_dir = Path(config["tmp_directory"])
    tmp_dir.mkdir(exist_ok=True, parents=True)

    out_path = extract_zipfile(source_path, tmp_dir)
    dir_name = str(out_path).split("/")[-1]
    next_ = list(out_path.glob("*"))[0]
    if next_.name[:10] == dir_name[:10] and next_.is_dir():
        out_path = next_
    elif next_.name == "ボイス" or next_.name == "特典壁紙":
        organize_image(out_path, config)
        out_path = out_path / "ボイス"

    liver_name, voice_category, is_EX = extract_file_info(
        dir_name, config["liver_info_path"]
    )

    target_dir = Path(config["voice_target_path"]) / liver_name / voice_category
    target_dir.mkdir(exist_ok=True, parents=True)

    for p in out_path.glob("*.mp3"):
        file_name = p.name
        shutil.copy(str(p), str(target_dir / file_name))
    shutil.copy(str(source_path), str(target_dir / source_path.name))


def is_voice_zipfile(source: Path, liver_info_path: str):
    file_name = source.name
    liver_info_df = pd.read_csv(liver_info_path)
    liver_name = "unkown"
    for name in liver_info_df["name"]:
        if name in file_name or name in file_name.replace("_", "・"):
            return True
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="choice voice zip file or donwload directory",
    )
    parser.add_argument(
        "--dir",
        "-d",
        action="store_true",
        help="if you select directory, please add this flag (default: False)",
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="laod from config's donwload_directory"
    )
    args = parser.parse_args()
    return args


def organize():
    args = parse_args()
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    if args.all:
        source = Path(config["download_directory"])
    else:
        source = source

    if args.dir or args.all:
        assert source.is_dir(), "Source is not directory"
        sources = sorted(
            [
                p
                for p in source.glob("*.zip")
                if is_voice_zipfile(p, config["liver_info_path"])
            ]
        )[::-1]

    else:
        assert source.exists(), "Source is not exsist"
        assert is_voice_zipfile(
            source, config["liver_info_path"]
        ), "Not nijisanji voice file"
        sorces = [source]

    with open("log.txt", "r") as f:
        logs = f.read().split("\n")[:-1]
    tmp_dir = Path(config["tmp_directory"])
    tmp_dir.mkdir(exist_ok=True, parents=True)

    for source in sources:
        # check already organize
        if (
            any(
                [log.replace(".zip", "") == source.name[: len(log) - 4] for log in logs]
            )
            and len(logs) > 0
        ):
            continue
        print(source.name)

        if "キービジュアル" in source.name:
            extracted_path = extract_zipfile(source, tmp_dir)
            next_ = list(extracted_path.glob("*"))[0]
            if next_.name[:10] == source.name[:10] and next_.is_dir():
                extracted_path = next_
            # voice
            voice_zips = list(extracted_path.glob("ボイス/*.zip"))

            for voice_zip in voice_zips:
                print("\t", voice_zip.name)
                organize_voice(voice_zip, config)
                logs.append(voice_zip.name)
                with open("log.txt", "a") as f:
                    f.write(voice_zip.name + "\n")
            # image
            organize_image(extracted_path, config)
        else:
            organize_voice(source, config)

        logs.append(source.name)
        with open("log.txt", "a") as f:
            f.write(source.name + "\n")

    shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    organize()
