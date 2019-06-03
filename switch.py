#!/usr/bin/env python3
# coding=utf-8
import glob
import sys
import os.path
import subprocess
from utils import Fore, parse_image_arg, probe_wsl, get_label, path_trans, handle_sigint

# handle arguments

handle_sigint()

if len(sys.argv) < 2:

	# print usage information

	print('usage: ./switch.py image[:tag]')

	# check if there are any installations

	basedir, lxpath, bashpath = probe_wsl(True)

	if basedir:
		#fix basedir to add LocalState\rootfs
		basedir = os.path.join(basedir, 'LocalState')
		names = glob.glob(os.path.join(basedir, 'rootfs*'))
		not_debian = True
		has_debian = False

		if len(names) > 0:

			print('\nThe following distributions are currently installed:\n')

			for name in names:
				active = os.path.basename(name) == 'rootfs'
				name   = get_label(name).split('_', 1)

				if len(name) != 2:
					continue

				if name[0] == 'debian' and name[1] == '9':
					has_debian = True

					if active:
						not_debian = False

				print('  - %s%s%s:%s%s%s%s' % (Fore.YELLOW, name[0], Fore.RESET, Fore.YELLOW, name[1], Fore.RESET, ('%s*%s' % (Fore.GREEN, Fore.RESET) if active else '')))

		if not_debian:
			print()

			if has_debian:
				print('To switch back to the default distribution, specify %sdebian%s:%s9%s as the argument.' % (Fore.YELLOW, Fore.RESET, Fore.YELLOW, Fore.RESET))
			else:
				print('You do not seem to have the default distribution installed anymore.\nTo reinstall it, run %slxrun /uninstall%s and %slxrun /install%s from the command prompt.' % (Fore.GREEN, Fore.RESET, Fore.GREEN, Fore.RESET))

	sys.exit(-1)

image, tag, fname, label = parse_image_arg(sys.argv[1], False)

# sanity checks

print('%s[*]%s Probing the Linux subsystem...' % (Fore.GREEN, Fore.RESET))

basedir, lxpath, bashpath = probe_wsl()
#fix basedir to add LocalState\rootfs
basedir = os.path.join(basedir, 'LocalState')

# read label of current distribution

clabel = get_label(os.path.join(basedir, 'rootfs'))

if not clabel:
	clabel = 'debian_9'

	if label == clabel:
		print('%s[!]%s No %s/.switch_label%s found, and the target rootfs is %subuntu%s:%strusty%s. Cannot continue.' % (Fore.RED, Fore.RESET, Fore.BLUE, Fore.RESET, Fore.YELLOW, Fore.RESET, Fore.YELLOW, Fore.RESET))
		print('%s[!]%s To fix this, run %secho some_tag > /.switch_label%s (replacing %ssome_tag%s with something like %sdebian_sid%s) from the current Bash terminal.' % (Fore.RED, Fore.RESET, Fore.GREEN, Fore.RESET, Fore.GREEN, Fore.RESET, Fore.GREEN, Fore.RESET))
		sys.exit(-1)
	else:
		print('%s[!]%s No %s/.switch_label%s found, assuming current rootfs is %subuntu%s:%strusty%s.' % (Fore.RED, Fore.RESET, Fore.BLUE, Fore.RESET, Fore.YELLOW, Fore.RESET, Fore.YELLOW, Fore.RESET))

# sanity checks, take two

if clabel == label:
	print('%s[!]%s The %s%s%s:%s%s%s rootfs is the current installation.' % (Fore.YELLOW, Fore.RESET, Fore.YELLOW, image, Fore.RESET, Fore.YELLOW, tag, Fore.RESET))
	sys.exit(-1)

if not os.path.isdir(os.path.join(basedir, 'rootfs_' + label)):
	print('%s[!]%s The %s%s%s:%s%s%s rootfs is not installed.' % (Fore.RED, Fore.RESET, Fore.YELLOW, image, Fore.RESET, Fore.YELLOW, tag, Fore.RESET))
	sys.exit(-1)

# do the switch

print('%s[*]%s Moving current %srootfs%s to %srootfs_%s%s...' % (Fore.GREEN, Fore.RESET, Fore.BLUE, Fore.RESET, Fore.BLUE, clabel, Fore.RESET))

try:
	subprocess.check_output(['cmd', '/C', 'move', path_trans(os.path.join(basedir, 'rootfs')), path_trans(os.path.join(basedir, 'rootfs_' + clabel))])

except subprocess.CalledProcessError as err:
	print('%s[!]%s Failed to backup current %srootfs%s: %s' % (Fore.RED, Fore.RESET, Fore.BLUE, Fore.RESET, err))
	sys.exit(-1)

print('%s[*]%s Moving desired %srootfs_%s%s to %srootfs%s...' % (Fore.GREEN, Fore.RESET, Fore.BLUE, label, Fore.RESET, Fore.BLUE, Fore.RESET))

try:
	subprocess.check_output(['cmd', '/C', 'move', path_trans(os.path.join(basedir, 'rootfs_' + label)), path_trans(os.path.join(basedir, 'rootfs'))])

except subprocess.CalledProcessError as err:
	print('%s[!]%s Failed to switch to new %srootfs%s: %s' % (Fore.RED, Fore.RESET, Fore.BLUE, Fore.RESET, err))
	print('%s[*]%s Rolling back to old %srootfs%s...' % (Fore.YELLOW, Fore.RESET, Fore.BLUE, Fore.RESET))

	try:
		subprocess.check_output(['cmd', '/C', 'move', path_trans(os.path.join(basedir, 'rootfs_' + clabel)), path_trans(os.path.join(basedir, 'rootfs'))])

	except subprocess.CalledProcessError as err:
		print('%s[!]%s Failed to roll back to old %srootfs%s: %s' % (Fore.RED, Fore.RESET, Fore.BLUE, Fore.RESET, err))
		print('%s[!]%s You are now the proud owner of one broken Linux subsystem! To fix it, run %slxrun /uninstall%s and %slxrun /install%s from the command prompt.' % (Fore.RED, Fore.RESET, Fore.GREEN, Fore.RESET, Fore.GREEN, Fore.RESET))

	sys.exit(-1)
