import os
import shutil
import subprocess

# Step1: 在根目录运行 pyinstaller main.py --noconsole --icon=Google_Translate_Icon.png --onefile
subprocess.call("pyinstaller main.py --noconsole --icon=Google_Translate_Icon.png --onefile", shell=True)

# Step2: 删除pyinstaller生成的除了可执行文件(main.exe)外的其他文件
os.remove("main.spec")
shutil.rmtree("build")

# Step3: 将可执行文件(main.exe)、根目录下所有.ui文件复制到一个文件夹中，文件夹叫JSON-i18n-release。完成此操作后删除dist文件夹
if not os.path.exists("JSON-i18n-release"):
    os.makedirs("JSON-i18n-release")

shutil.move("dist/main.exe", "JSON-i18n-release/")
for file in os.listdir("."):
    if os.path.isfile(file) and file.endswith(".ui"):
        shutil.copy(file, "JSON-i18n-release/")

shutil.rmtree("dist")

# Step4: 使用winrar压缩这个文件夹为zip
subprocess.call('"D:\winrar\Rar.exe" a -r JSON-i18n-release.zip JSON-i18n-release', shell=True)

# Step5: 使用winrar为这个zip生成自解压模块，模块使用zip.sfx。
subprocess.call('"D:\winrar\Rar.exe" s -zzip.sfx JSON-i18n-release.zip', shell=True)

# Step6: 删除JSON-i18n-release.zip、JSON-i18n-release文件夹
os.remove("JSON-i18n-release.zip")
shutil.rmtree("JSON-i18n-release")
