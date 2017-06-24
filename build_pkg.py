import shutil
import glob
import os


def copy_file_or_dir(src, dst):
    """
    Copy files or directories to the dst folder. Ignore __pycache__ and
    easy_install.sh
    """
    if "__pycache__" in src or "easy_install.py" in src:
        return

    print("copying {}".format(src))
    try:
        shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
    except NotADirectoryError:
        shutil.copy(src, dst)


def main():
    """
    Package mpgen and dependent Python packages into zip for uploading to
    AWS Lambda instance
    """
    package_name = "mpgen.py"
    tmpdir = "mpgen.tmp"

    # remove leftover folders we are about to make
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    if os.path.exists("mpgen.zip"):
        os.remove("mpgen.zip")

    # make tmp working dir
    os.mkdir(tmpdir)
    os.mkdir(os.path.join(tmpdir, "mpgen"))

    # copy src files
    for f in glob.glob("mpgen/*.py"):
        copy_file_or_dir(f, os.path.join(tmpdir, "mpgen"))

    # copy packages
    for f in glob.glob("venv/Lib/site-packages/*"):
        copy_file_or_dir(f, tmpdir)

    # copy main module
    with open("run.py") as fread:
        lines = fread.readlines()

    # write run.py but replace if __main__ section with AWS Lambda function
    with open(os.path.join("mpgen.tmp", "mpgen_runner.py"), "w") as fwrite:
        for line in lines:
            if "if __name__" in line:
                break
            fwrite.write(line)

        fwrite.write("""\
def lambda_handler(event, context):
    run()
""")

    # zip everything up and remove tmp folder
    shutil.make_archive("mpgen", "zip", tmpdir)
    shutil.rmtree(tmpdir)

if __name__ == "__main__":
    main()
