import os

curr_dir = os.path.dirname(__file__)
opend_prefix = "Futu_OpenD_"
dir_names = os.listdir(curr_dir)
for dir_name in dir_names:
    if dir_name.startswith(opend_prefix):
        break

executable_path = os.path.join(curr_dir,dir_name,"FutuOpenD")
account = "enter your own account number"
password = "enter your own account password"