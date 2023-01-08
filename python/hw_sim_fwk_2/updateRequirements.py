# alternatively run in your console (with internet connection!):
# > pipreqs --force ./ --ignore backups
# ##############################################################
import shlex
import subprocess


print("Updating requirements.txt..")
# shell=True generates a high severity vulnerability warning when running bandit - so we set it to False instead..
p1 = subprocess.Popen(shlex.split("pipreqs --force ./ --ignore backups"), shell=False)  # True)
p1.wait()
p1.terminate()
p1.kill()
