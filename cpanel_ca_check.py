#!/usr/bin/env python

import sys
import os
import optparse
import glob
import errno
import subprocess
import traceback
import logging

parser = optparse.OptionParser()
parser.add_option('-u', '--user', dest='user', help='Specify the user using autossl you want to check for a contained certificate authority bundle')

(options, args) = parser.parse_args()

# Define function to be used for finding the last modified file in a directory based on a glob string
def lastModified(directory, search):
    try:
        if os.path.isdir(directory):
            newest = max(glob.iglob(os.path.join(directory, search)), key=os.path.getmtime)
            return newest
        else:
            raise ValueError('Passed Directory Does not Exist!', directory)
    except ValueError as err:
        print(err.args)

# Define function to be used for checking the number of occurances in a file of a particular string
def countString(file, string):

    count = 0
    file_lines = open(file, 'r')

    for line in file_lines:
        if string in line:
            count += 1

    return count

# Define function to be used for adding the ca bundle to the bottom of the certificate to prevent certificate incomplete errors.
def addBundle(user, cert_file):

    try:
        # Ensure the certificate file is formatted for the id
        cert_file = cert_file.replace('.crt', '')
        cert_file = cert_file.split('/')[-1]

        # Fetch the cabundle using the UAPI
        print('Fetching cabundle from cPanel using UAPI')
        uapi_cmd = "uapi --user=" + user + " SSL fetch_cert_info id=" + cert_file
        process = subprocess.Popen(uapi_cmd.split(), stdout=subprocess.PIPE)
        output, err = process.communicate()

        # Seperate out the response and get the bundles from the response
        output = output.split()
        bundle_begin = output.index('cabundle:')
        bundle_end = output.index('certificate:')

        bundle = ""
        first = 0

        for index in range(int(bundle_begin + 1), bundle_end):

            if first == 0:
                bundle = '\n' + bundle + output[index]
                first = 1

            else:
                bundle = bundle + " " + output[index]

        # Ensure the file is correctly formatted to be appended to the other documents
        bundle = bundle.replace("\\n", "\n")
        bundle = bundle.replace('"', '')

        # Append the bundle to the original certificate file
        export = open('/home/' + user + '/ssl/certs/' + cert_file + '.crt', "a")
        export.write(bundle)
        export.close()
        print('Appended to file successfully')

    except Exception as e:
        print(e)
        logging.error(traceback.format_exc())

usrdir_cert = '/home/' + options.user + '/ssl/certs/'
certificate = lastModified(usrdir_cert, '*.crt')

if countString(certificate, 'BEGIN CERTIFICATE') < 2:

    print('User: ' + options.user)
    print('CA Bundle Not Included')
    addBundle(options.user, certificate)

    # Reloads nginx configuration, can be removed on servers not utilising nginx ssl termination
    subprocess.call('/root/scripts/cron/nginx/nginx_reload')
