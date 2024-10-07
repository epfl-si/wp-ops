#!/bin/bash
# https://www.jimangel.io/posts/automate-ubuntu-22-04-lts-bare-metal
# https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html
# https://cloudinit.readthedocs.io/en/latest/reference
# https://cloudinit.readthedocs.io/en/latest/howto/run_cloud_init_locally.html
# https://multipass.run/install
# test locally with
# multipass launch noble --name test-vm --cloud-init 00/user-data
# multipass shell test-vm 

# multipass launch noble --name testvm1 --network name=en0,mode=auto,mac=E2:B3:BC:CE:CF:1F --cloud-init mods/00/user-data
# multipass launch noble --name testvm1 --network name=en0,mode=auto,mac=CE:5E:B2:AF:B7:E6 --cloud-init mods/00/user-data
# multipass delete -p testvm1  
# multipass delete -p testvm2

# set -x
set -e

# first cli argument is eventually a version number for the user-data file
v=$1

die() {
	echo "$*" >&2
	exit 1
}

ISOBASE=data/base.iso
BOOT=data/BOOT
MBR=data/base.mbr
EFI=data/base.efi
ISOFINAL=data/ubuntu24_fsd_autoinstall_gc.iso
FSDIR=data/src
AUTODIR=$FSDIR/server
NONETDIR=$FSDIR/servernn
CFGDIR=$FSDIR/config
UBUNAME=noble
DOCKIMG=nero:0
KB=/keybase/team/epfl_wp_test
SSHKEYS='azecko d4rkheart domq dragonleman dwesh163 Jch4ipas jdelasoie lvenries multiscan obieler ponsfrilus rosamaggi saskyapanchaud'

which xorriso || die "xorriso not installed"

[ -f $ISOBASE ] || curl -o $ISOBASE https://cdimage.ubuntu.com/ubuntu-server/${UBUNAME}/daily-live/current/${UBUNAME}-live-server-amd64.iso
if [ ! -d $FSDIR ] ; then
  [ -d $BOOT ] && mv $BOOT $BOOT.$(date +%F.%s)
  7zz -y x $ISOBASE  -o$FSDIR
  mv "$FSDIR/[BOOT]" $BOOT
fi

cp mods/grub.cfg $FSDIR/boot/grub/grub.cfg

[ -d $AUTODIR ] && rm -rf $AUTODIR
mkdir $AUTODIR
cp mods/user-data$v.yml $AUTODIR/user-data
touch $AUTODIR/meta-data

[ -d $NONETDIR ] && rm -rf $NONETDIR
mkdir $NONETDIR
cp mods/user-data${v}-nonet.yml $NONETDIR/user-data
touch $NONETDIR/meta-data

[ -d $CFGDIR ] && rm -rf $CFGDIR
mkdir $CFGDIR
cp -R $KB/wpn_k8s_hosts $CFGDIR/hosts
if [ ! -f data/authorized_keys ] ; then
  echo "Regenerating mods/authorized_keys file"
  for k in $SSHKEYS ; do
    curl https://github.com/$k.keys >> data/authorized_keys
  done
fi  
cp data/authorized_keys $CFGDIR/authorized_keys

xorriso -as mkisofs -r \
  -V 'Ubuntu 24 FSD AUTO (EFIBIOS)' \
  --grub2-mbr $BOOT/1-Boot-NoEmul.img \
  -partition_offset 16 \
  --mbr-force-bootable \
  -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b $BOOT/2-Boot-NoEmul.img \
  -appended_part_as_gpt \
  -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \
  -c '/boot.catalog' \
  -b '/boot/grub/i386-pc/eltorito.img' \
    -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \
  -eltorito-alt-boot \
  -e '--interval:appended_partition_2:::' \
  -no-emul-boot \
  -o ${ISOFINAL} \
  $FSDIR

echo "Install CD image update. Please upload it to xaas NAS"
echo "$(PWD)/$ISOFINAL"
echo "smb://nassvmmix01.epfl.ch/si_vsissp_iso_priv_repo_p01_app/ITServices/its_wbhst"
