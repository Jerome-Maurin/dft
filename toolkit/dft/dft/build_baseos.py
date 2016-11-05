#
# The contents of this file are subject to the Apache 2.0 license you may not
# use this file except in compliance with the License.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
#
# Copyright 2016 DFT project (http://www.debianfirmwaretoolkit.org).  
# All rights reserved. Use is subject to license terms.
#
# Debian Firmware Toolkit is the new name of Linux Firmware From Scratch
# Copyright 2014 LFFS project (http://www.linuxfirmwarefromscratch.org).  
#
#
# Contributors list :
#
#    William Bonnet     wllmbnnt@gmail.com, wbonnet@theitmakers.com
#
#

import logging, os, subprocess, tarfile, shutil, tempfile, distutils
from distutils import dir_util, file_util

#
#    Class BuildBaseOS
#
class BuildBaseOS: 
    """This class implements method needed to create the base OS

       The "base OS" is the initial installation of Debian (debootstrap) which
       is used to apply ansible playbooks.

       The methods implemented in this class provides what is needed to :
         . create the debootstrap (chrooted environment)
         . handle filesystems like dev and proc in the chrooted environment
         . copy DFT and project specific templates into /dft_bootstrap
         . run ansible in the chroot
         . cleanup things when installation is done
    """

    # -------------------------------------------------------------------------
    #
    # __init__
    #
    # -------------------------------------------------------------------------
    def __init__(self, project):
        """Default constructor
        """

        # Object storing the project definition. Project holds all the 
        # configuration and definition used by the different stage of 
        # the toolchain, including baseos definition
        self.project = project

        # Retrieve the architecture of the host
        self.host_arch = subprocess.check_output("dpkg --print-architecture", shell=True).decode('UTF-8').rstrip()

        # Boolean used to flag the use of QEMU static
        self.use_qemu_static =  (self.host_arch != project.target_arch)

        # Boolean used to flag if the cache archive is available. This value 
        # is set by the setup_configuration method. Default is False, to 
        # ensure it will be rebuild
        self.cache_archive_is_available = False
 
        # Flags used to remove 'mount bind' states
        self.proc_is_mounted   = False
        self.devpts_is_mounted = False
        self.devshm_is_mounted = False

        # Flag used to prevent multiple call to cleanup since cleanup is used
        # in exception processing
        self.doing_cleanup_installation_files = False

        # Set the log level from the configuration
        logging.basicConfig(level=project.dft.log_level)

    # -------------------------------------------------------------------------
    #
    # install_baseos
    #
    # -------------------------------------------------------------------------
    def install_baseos(self):
        """This method implement the logic of generating the rootfs. It calls
        dedicated method for each step. The main steps are :

        . setting up configuration
        . extracting cache archive content or running debootstrap
        . setup QEMU and run stage 2 if needed
        . update cache if needed
        . deploy DFT Ansible templates, and run Ansible to do confiugration
        . cleanup installation files
        . cleanup QEMU
        """

        # Check that DFT path is valid
        if os.path.isdir(self.project.dft.dft_source_path) == False:
            logging.critical("Path to DFT installation is not valid : %s",  self.project.dft.dft_source_path)
            exit(1)

        # Ensure target rootfs mountpoint exists and is a dir
        if os.path.isdir(self.project.rootfs_mountpoint) == False:
            os.makedirs(self.project.rootfs_mountpoint)
        else:
            logging.warn("target rootfs mount point already exists : " + self.project.rootfs_mountpoint)

        # Check if the archive has to be used instead of doing a debootstraping
        # for real. Only if the archive exist...
        if self.project.dft.use_cache_archive == True and self.cache_archive_is_available == True:
            self.fake_generate_debootstrap_rootfs()
        else:
            # In any other cases, do a real debootstrap call
            self.generate_debootstrap_rootfs()

        # þest the archive has to be updated
        if self.project.dft.update_cache_archive == True:
            # But only do it if we haven't bee using the cache, or it
            # would be extracted, then archived again.
            if self.project.dft.use_cache_archive == True:
                self.update_rootfs_archive()

        # Launch Ansible to install roles identified in configuration file
        self.install_packages()

        # Once installation has been played, we need to do some cleanup
        # like ensute that no mount bind is still mounted, or delete the
        # DFT ansible files
        self.cleanup_installation_files()

        # Remove QEMU if it has been isntalled. It has to be done in the end
        # since some cleanup tasks could need QEMU
        if self.use_qemu_static == True:
            self.cleanup_qemu()



    # -------------------------------------------------------------------------
    #
    # run_ansible
    #
    # -------------------------------------------------------------------------
    def install_packages(self):
        """This method remove the QEMU static binary which has been previously 
        copied to the target 
        """

        logging.info("installing packages...")

        # Create the target directory. DFT files will be installed under this
        # directory.
        try:
            logging.debug("copying DFT toolkit...")

            # Create the target directory in the rootfs
            dft_target_path = self.project.rootfs_mountpoint + "/dft_bootstrap/"
            if not os.path.exists(dft_target_path):
                os.makedirs(dft_target_path)

            # Copy the DFT toolkit content to the target rootfs
            for target_to_copy in os.listdir(self.project.dft.dft_source_path):
                logging.debug("Copy the DFT toolkit : preparing to copy " + target_to_copy)
                target_to_copy_path = os.path.join(self.project.dft.dft_source_path, target_to_copy)
                if os.path.isfile(target_to_copy_path):
                    logging.debug("copying file " + target_to_copy_path + " => " + dft_target_path)
                    distutils.file_util.copy_file(target_to_copy_path, dft_target_path)
                else:
                    logging.debug("copying tree " + target_to_copy_path + " => " + dft_target_path)
                    distutils.dir_util.copy_tree(target_to_copy_path, os.path.join(dft_target_path, target_to_copy))

            # Copy the additional toolkit content to the target rootfs
            for additional_path in self.project.dft_additional_path:
                logging.debug("Copy the additional toolkit : preparing to copy from additional path " + additional_path)
                for target_to_copy in os.listdir(additional_path):
                    logging.debug("Copy the additional toolkit : preparing to copy " + target_to_copy)
                    target_to_copy_path = os.path.join(additional_path, target_to_copy)
                    if os.path.isfile(target_to_copy_path):
                        logging.debug("copying file " + target_to_copy_path + " => " + dft_target_path)
                        distutils.file_util.copy_file(target_to_copy_path, dft_target_path)
                    else:
                        logging.debug("copying tree " + target_to_copy_path + " => " + dft_target_path)
                        distutils.dir_util.copy_tree(target_to_copy_path, os.path.join(dft_target_path, target_to_copy))

        except OSError as e:
            # Call clean up to umount /proc and /dev
            self.cleanup_installation_files()
            logging.critical("Error: %s - %s." % (e.filename, e.strerror))
            exit(1)

        except shutil.Error as e:
            self.cleanup_installation_files()
            logging.critical("Error: %s - %s." % (e.filename, e.strerror))
            exit(1)
     
        # Copy the project roles to the target rootfs

        # Execute Ansible
        logging.info("running ansible...")
        for ansible_target in self.project.dft_ansible_targets:
            sudo_command = "LANG=C sudo chroot " + self.project.rootfs_mountpoint + " /bin/bash -c \"cd /dft_bootstrap && /usr/bin/ansible-playbook -i inventory.yml -c local " + ansible_target + ".yml\""
            self.execute_command(sudo_command)
        logging.info("ansible stage successfull")
    


    # -------------------------------------------------------------------------
    #
    # setup_qemu
    #
    # -------------------------------------------------------------------------
    def setup_qemu(self):
        """This method remove the QEMU static binary which has been previously 
        copied to the target 
        """

        # We should not execute if the flag is not set. Should have already 
        # been tested, but double check by security
        if self.use_qemu_static != True:
            return

        # Copy the QEMU binary to the target, using root privileges
        if   self.project.target_arch == "armhf":   qemu_target_arch = "arm"
        elif self.project.target_arch == "armel":   qemu_target_arch = "arm"
        else:                                       qemu_target_arch = self.project.target_arch

        logging.info("setting up QEMU for arch " + self.project.target_arch + " (using /usr/bin/qemu-" + qemu_target_arch + "-static)")
        sudo_command = "sudo cp /usr/bin/qemu-"  + qemu_target_arch + "-static " + self.project.rootfs_mountpoint + "/usr/bin/"
        self.execute_command(sudo_command)



    # -------------------------------------------------------------------------
    #
    # cleanup_qemu
    #
    # -------------------------------------------------------------------------
    def cleanup_qemu(self):
        """This method copy the QEMU static binary to the target 
        """

        # We should not execute if the flag is not set. Should have already 
        # been tested, but double check by security
        if self.use_qemu_static != True:
            return

        if self.project.dft.keep_bootstrap_files == True:
            logging.debug("keep_bootstrap_files is activated, keeping QEMU in " + self.project.rootfs_mountpoint)
            return

        # Copy the QEMU binary to the target, using root privileges
        if   self.project.target_arch == "armhf":   qemu_target_arch = "arm"
        elif self.project.target_arch == "armel":   qemu_target_arch = "arm"
        else:                                       qemu_target_arch = self.project.target_arch
        
        # Execute the file removal with root privileges
        logging.info("cleaning QEMU for arch " + self.project.target_arch + "(/usr/bin/qemu-" + qemu_target_arch + "-static)")
        os.system("sudo rm " + self.project.rootfs_mountpoint + "/usr/bin/qemu-" + qemu_target_arch + "-static")



    # -------------------------------------------------------------------------
    #
    # cleanup_installation_files
    #
    # -------------------------------------------------------------------------
    def cleanup_installation_files(self):
        """This method is incharge of cleaning processes after Ansible has been 
        launched. In some case some daemons are still running inside the 
        chroot, and they have to be stopped manually, or even killed in order
        to be able to umount /dev/ and /proc from inside the chroot
        """
        logging.info("starting to cleanup installation files")

        # Are we already doing a cleanup ? this may happens if an exception
        # occurs when cleaning up. It prevents multiple call and loop in
        # exception processing
        if self.doing_cleanup_installation_files == True:
            return

        # Set the flag used to prevent multiple call
        self.doing_cleanup_installation_files = True

        # Check if /proc is mounted, then umount it
        if self.proc_is_mounted == True:
            sudo_command = "sudo umount " + self.project.rootfs_mountpoint + "/dev/pts"
            self.execute_command(sudo_command)

        # Check if /dev/shm is mounted, then umount it
        if self.devshm_is_mounted == True:
            sudo_command = "sudo umount " + self.project.rootfs_mountpoint + "/dev/shm"
            self.execute_command(sudo_command)

        # Check if /dev/pts is mounted, then umount it
        if self.devpts_is_mounted == True:
            sudo_command = "sudo umount " + self.project.rootfs_mountpoint + "/proc"
            self.execute_command(sudo_command)

        self.doing_cleanup_installation_files = False

        # Delete the DFT files from the rootfs
        if self.project.dft.keep_bootstrap_files == False:
            shutil.rmtree(self.project.rootfs_mountpoint + "/dft_bootstrap")
        else:
            logging.debug("keep_bootstrap_files is activated, keeping DFT bootstrap files in " + self.project.rootfs_mountpoint + "/dft_bootstrap")



    # -------------------------------------------------------------------------
    #
    # generate_build_number
    #
    # -------------------------------------------------------------------------
    def generate_build_number(self):
        """ Generate a version number in /etc/dft_version file. This is used
        to keep track of generation date.
        """

        logging.info("starting to generate build number")

        # Open the file and writes the timestamp in it
        filepath = self.project.rootfs_mountpoint + "/etc/dft_version"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("DFT-" + self.project.timestamp + "\n")
        f.close()

        sudo_command = "sudo mv -f " + f.name + " " + filepath
        self.execute_command(sudo_command)


    # -------------------------------------------------------------------------
    #
    # update_rootfs_archive
    #
    # -------------------------------------------------------------------------
    def update_rootfs_archive(self):
        """This methods update (delete then recreate) the rootfs archive after
        doing a real debootstrap installation.

        Archive is not updated if cache has been used instead of debootstraping
        otherwise it would generate the same archive"""
        logging.info("starting to update rootfs archive")

        # Remove existing archive before generating the new one
        try:
            if os.path.isfile(self.project.archive_filename) == True:
                logging.info("removing previous archive file : " + self.project.archive_filename)
                os.remove(self.project.archive_filename)

        # Catch file removal exceptions
        except OSError as e:
            logging.critical("Error: %s - %s." % (e.filename, e.strerror))
            self.cleanup_installation_files()
            exit(1)

        # Create the new archive
        cache_archive = tarfile.open(self.project.archive_filename)
        cache_archive.add(name=self.project.rootfs_mountpoint)
        cache_archive.close()



    # -------------------------------------------------------------------------
    #
    # fake_generate_debootstrap_rootfs
    #
    # -------------------------------------------------------------------------
    def fake_generate_debootstrap_rootfs(self):
        logging.info("starting to fake generate debootstrap rootfs")

        # Check that the archive exists
        if os.path.isfile(self.project.archive_filename) == False:
            logging.warning("cache has been activate and archive file does not exist : " + self.archive_filename)
            return False

        # Extract tar file to rootfs mountpoint
        logging.info("extracting archive : " + self.project.archive_filename)
        cache_archive = tarfile.open(self.project.archive_filename)
        cache_archive.extractall(path=self.project.rootfs_mountpoint)
        cache_archive.close()



    # -------------------------------------------------------------------------
    #
    # generate_debootstrap_rootfs
    #
    # -------------------------------------------------------------------------
    def generate_debootstrap_rootfs(self):
        """
        """

        logging.info("starting to generate debootstrap rootfs")

        # Generate the base debootstrap command
        debootstrap_command  = "sudo debootstrap --no-check-gpg"

        # Add the foreign and arch only if they are different from host, and
        # thus if use_qemu_static is True
        if self.use_qemu_static == True:
            logging.info("running debootstrap stage 1")
            debootstrap_command += " --foreign --arch=" + self.project.target_arch 
        else:
            logging.info("running debootstrap")

        # Add the target, mount point and repository url to the debootstrap command
        debootstrap_command += " " +  self.project.target_version + " " + self.project.rootfs_mountpoint + " " + self.project.baseos.pkg_archive_url

        # Finally run the subprocess
        self.execute_command(debootstrap_command)

        # Check if we are working with foreign arch, then ... 
        if self.use_qemu_static == True:
            # QEMU is used, and we have to install it into the target
            self.setup_qemu()

            # And second stage must be run
            logging.info("doing debootstrap stage 2")
            debootstrap_command  = "LANG=C sudo chroot " + self.project.rootfs_mountpoint + " /debootstrap/debootstrap --second-stage"
            self.execute_command(debootstrap_command)


        # Mount bind /proc into the rootfs mountpoint
        sudo_command = "sudo mount --bind --make-rslave /proc " + self.project.rootfs_mountpoint + "/proc"
        self.execute_command(sudo_command)
        self.proc_is_mounted = True

        # Mount bind /dev/pts into the rootfs mountpoint
        sudo_command = "sudo mount --bind --make-rslave /dev/pts " + self.project.rootfs_mountpoint + "/dev/pts"
        self.execute_command(sudo_command)
        self.devpts_is_mounted = True

        # Mount bind /dev/shm into the rootfs mountpoint
        sudo_command = "sudo mount --bind --make-rslave /dev/shm " + self.project.rootfs_mountpoint + "/dev/shm"
        self.execute_command(sudo_command)
        self.devshm_is_mounted = True

        # Update the APT sources
        self.generate_apt_sources_configuration()

        # Then update the list of packages
        apt_command = "sudo chroot " + self.project.rootfs_mountpoint + " /usr/bin/apt-get update"
        self.execute_command(apt_command)
 
        # Install extra packages into the chroot
        apt_command = "sudo chroot " + self.project.rootfs_mountpoint + " /usr/bin/apt-get install --no-install-recommends --yes --allow-unauthenticated apt-utils ansible"
        self.execute_command(apt_command)

        # Generate a unique build timestamp into /etc/dft_version 
        self.generate_build_number()



    # -------------------------------------------------------------------------
    #
    # generate_apt_sources_configuration
    #
    # -------------------------------------------------------------------------
    def generate_apt_sources_configuration(self):
        """ This method has two functions, configure APT sources and configure
        apt to ignore validity check on expired repositories

        The method generates a file named 10no-check-valid-until which is 
        placed in the apt config directory. It is used to deactivate validity
        check on repository during installation, so a mirror can still be used
        even if it is expired. This use case happens often when mirrors cannot
        be sync'ed automatically from the internet

        Second part of the methods iterate the repositories from configuration
        file and generates sources.list
        """
#TODO : remove validity check after generation ? => flag ? 
        logging.info("starting to generate APT sources configuration")

        # Generate the file path
        filepath = self.project.rootfs_mountpoint + "/etc/apt/apt.conf.d/10no-check-valid-until"

        # Open the file and writes configuration in it
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("Acquire::Check-Valid-Until \"0\";\n")
        f.close()

        sudo_command = "sudo mv -f " + f.name + " " + filepath
        self.execute_command(sudo_command)

        # Generate the file path
        filepath = self.project.rootfs_mountpoint + "/etc/apt/sources.list"

        # Open the file and writes configuration in it
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("deb " + self.project.baseos.debian_mirror_url + "/debian " + self.project.target_version + " main contrib non-free\n")
            f.write("deb " + self.project.baseos.debian_mirror_url + "/debian-security " + self.project.target_version + "/updates main contrib non-free\n")
            f.write("deb " + self.project.baseos.debian_mirror_url + "/debian " + self.project.target_version + "-updates main contrib non-free\n")
        f.close()

        sudo_command = "sudo mv -f " + f.name + " " + filepath
        self.execute_command(sudo_command)

    # -------------------------------------------------------------------------
    #
    # exec_sudo
    #
    # -------------------------------------------------------------------------
    def execute_command(self, command):
        """ This method run a command as a subprocess. Typical use case is 
        running sudo commands.

        This method is a wrapper to subprocess.run , and will be moved soon
        in a helper object. It provides mutalisation of error handling
        """

        try:
            logging.debug("running : " + command)
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)

        except subprocess.CalledProcessError as e:
            self.cleanup_installation_files()
            logging.critical("Error %d occured when executing %s" % (e.returncode, e.cmd))
            logging.debug("stdout")
            logging.debug("%s" % (e.stdout.decode('UTF-8')))
            logging.debug("stderr")
            logging.debug("%s" % (e.stderr.decode('UTF-8')))
            exit(1)