# u-boot installation for orangepi-zero

## Disclaimer

This procedure is provided as is, and should be check by yourself before
blindly executing it. Errors in the procedure it self, or user errors when
applying the procedure may result in irreversible data loss, or even bricking
the board.

You have been warned :)

## u-boot installation

The u-boot binary to install has been copied by this package to :
/boot/u-boot/u-boot-orangepi-zero

This is a symlink to the current u-boot file stored at the same location in a
file named u-boot-orangepi-zero.VERSION

u-boot binary has to be installed on the first sectors of the device used by 
the board to boot. This can be done by the following commands, assuming that :

. The commands are run as root or using sudo ( that's the example)

. The commands are run on the target board (orangepi-zero)

. Which means the /dev/mmcblk0 is the internal CF card used to boot

First the commands will cleanup the sectors used on the flash, then copy the
u-boot itself.

 
## shell commands

sudo dd if=/dev/zero of=/dev/mmcblk0 bs=1k count=1023 seek=1 status=noxfer
sudo dd if=/boot/u-boot/u-boot-orangepi-zero of=/dev/mmcblk0 bs=1024 seek=8 status=noxfer
