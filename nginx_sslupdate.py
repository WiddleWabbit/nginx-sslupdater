#!/usr/bin/env python

###                                               AutoSSL NGinx Symlink Update                                                ###

#   This script checks to see if Cpanels Autossl has installed a new SSL certificate by looking to see if the latest certificate
#   in the users ssl folder has changed. If it has, it updates the symlinks for nginx so that it is using the latest ssl certificate.
#   Following this it restarts nginx to save the changes.

#   In order to use the script pass it the argument -u and the user to run the script for



##   Import sys in order to store any variables passed in the run command

import sys, os, optparse, glob, errno, subprocess

##   Create option for user input

parser = optparse.OptionParser()
parser.add_option('-u', '--user', dest='user', help='The user to update nginx autoSSL for')

(options, args) = parser.parse_args()


##   Check to see a user was submitted with command

if options.user is None:

#   If user ask for a user and close
    print 'Please input user'
    sys.stdout.flush()
    sys.exit(0)

else:

#   Define Variables for the current path of the symlinks, certificates/keys and the users directories housing the certificates/keys
    current_sym_cert = '/etc/nginx/symlinks/' + options.user + '_current_cert'
    current_sym_key = '/etc/nginx/symlinks/' + options.user + '_current_key'
    current_cert = os.path.realpath ( current_sym_cert )
    current_key = os.path.realpath ( current_sym_key )
    usrdir_cert = '/home/' + options.user + '/ssl/certs/'
    usrdir_key = '/home/' + options.user + '/ssl/keys/'

#   Use glob to find the most recent certificate file and the most recent key file from the users directory
    newest_cert = max(glob.iglob(os.path.join(usrdir_cert, '*.crt')), key=os.path.getmtime)
    newest_key = max(glob.iglob(os.path.join(usrdir_key, '*.key')), key=os.path.getmtime)

#   Check to see if the latest certificate and the latest key are both the same as the current ones, if so then exit
    if current_cert == newest_cert and current_key == newest_key:

        sys.exit(0)

#   Otherwise Update the symlinks to reference the latest key and certificate, then restart nginx by calling a bash script
    else:

        print 'AutoSSL nginx certificate and key symlinks require update\n'
        sys.stdout.flush()

#   Define function to be used in replacing symlinks, function trys to create the link and if it cant because one already exists it deletest the old one and
#   then trys to create it again. If it fails in creation due to another error then it prints the error.
        def symlink_force(target, link_name):

            try:

                os.symlink(target, link_name)
        
            except OSError, e:

                if e.errno == errno.EEXIST:
                    os.remove(link_name)
                    os.symlink(target, link_name)
                    print 'Replaced Existing Symlink For: ',options.user
                    sys.stdout.flush()

                else:
                    raise e

#   Call symlink_force function to replace symlinks with symlinks to the latest certificates
        symlink_force(newest_cert, current_sym_cert)
        symlink_force(newest_key, current_sym_key)

#   Restart nginx by calling nginx_restart script
        print 'Attempt nginx restart\n'
        sys.stdout.flush()
        subprocess.call('/root/scripts/cron/nginx/nginx_reload')
