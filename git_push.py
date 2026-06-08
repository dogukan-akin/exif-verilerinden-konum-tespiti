import os
import subprocess

# Ensure Git is in path
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Git\cmd"

def run(cmd):
    print("Running:", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error:", result.stderr)
    else:
        print(result.stdout)

run("git config --global user.email \"dogukan.akin@example.com\"")
run("git config --global user.name \"Dogukan Akin\"")
run("git init")
run("git branch -M main")
run("git remote remove origin")
run("git remote add origin https://github.com/dogukan-akin/exif-verilerinden-konum-tespiti.git")
run("git add .")
run("git commit -m \"Initial commit\"")
print("Opening browser for authentication...")
run("git push -u origin main")
