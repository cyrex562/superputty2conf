# Host aws-bridge
# Hostname 52.11.179.66
# IdentityFile ~/.ssh/jm-office-bridge-key.pem
# User ubuntu

# < SessionData
# SessionId = "bridge/cliqr-4.5/cliqr cco"
# SessionName = "cliqr cco"
# ImageKey = "computer"
# Host = "10.201.1.79"
# Port = "22"
# Proto = "SSH"
# PuttySession = "Default Settings"
# Username = "centos"
# ExtraArgs = "-i E:\ts16\cliqr\cliqr_private_key.ppk"
# SPSLFileName = "" / >
import os
import sys
from bs4 import BeautifulSoup
import re
import logging
import ntpath
import argparse

argparser = argparse.ArgumentParser(description="convert statements in superputty sessions file to user ssh conf file entries")
argparser.add_argument("--in_file", help="the path to the sessions file")
argparser.add_argument("--out_file", help="the path to the output file to create. overwritten if it exists.")
argparser.add_argument("--key_path", help="the path where keys with the same names in the sessions file exist.")
args = argparser.parse_args()

SESSION_DATA_FORMAT = "Host {}\r\n" \
                      "Hostname {}\r\n" \
                      "User {}\r\n"

KEY_DATA_FORMAT = "IdentityFile {}".format(args.key_path) + "/{}\r\n"

PWD_DATA_FORMAT = "# Password {}\r\n"

LOG_FORMATTER_STR = "%(asctime)s: %(levelname)s: %(module)s: %(message)s"

logger = logging.getLogger("superputty2conf")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt=LOG_FORMATTER_STR)

stdout_stream_handler = logging.StreamHandler(stream=sys.stdout)
stdout_stream_handler.setLevel(logging.DEBUG)
stdout_stream_handler.setFormatter(formatter)
logger.addHandler(stdout_stream_handler)

stderr_stream_handler = logging.StreamHandler(stream=sys.stderr)
stderr_stream_handler.setFormatter(formatter)
stderr_stream_handler.setLevel(logging.ERROR)
logger.addHandler(stderr_stream_handler)


logger.info("opening sessions file")

in_b = ''
try:
    in_f = open(args.in_file, 'r')
    in_b = in_f.read()
    in_f.close()
except Exception as e:
    logger.exception("reading input file failed: ", e)

logger.info("parsing xml")
soup = BeautifulSoup(in_b, "xml")

conf_buf = ''
a = soup.ArrayOfSessionData
sessions = a.find_all('SessionData')
for s in sessions:
    logger.debug("session xml: \"{}\"".format(str(s)))
    host_str = re.sub('[^0-9a-zA-Z]+', '_', s['SessionName']).lower()
    host_str = re.sub('_+]', "_", host_str)
    host_name_str = s['SessionName']
    user_str = s['Username']
    extra_args_str = s['ExtraArgs']

    key_file_name = ''
    pwd = ''
    if len(extra_args_str) > 0:
        if extra_args_str.find('-i') != -1:
            logger.debug("session has key file")
            norm_path = os.path.normpath(extra_args_str)
            key_file_name = os.path.split(norm_path)[-1]
            nt_key_file_name = ntpath.split(norm_path)[-1]
            if len(key_file_name) > len(nt_key_file_name):
                key_file_name = nt_key_file_name
            key_file_name = key_file_name.replace(".ppk", ".pem")
        elif extra_args_str.find('-pw') != -1:
            logger.debug("session has password")
            pwd = extra_args_str.split(" ")[1]

    session_str = SESSION_DATA_FORMAT.format(host_str, host_name_str, user_str)
    if len(key_file_name) > 0:
        session_str += KEY_DATA_FORMAT.format(key_file_name)
    if len(pwd) > 0:
        session_str += PWD_DATA_FORMAT.format(pwd)
    session_str += '\r\n'

    logger.debug("output session text: {}".format(session_str))
    conf_buf += session_str


logger.info("writing sessions to conf file")
out_f = open(args.out_file, 'w+')
out_f.write(conf_buf)
out_f.close()

# END OF FILE #
