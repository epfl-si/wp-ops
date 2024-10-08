# Ubuntu autoinstall ISO
This directory is dedicated to the generation for an autoinstall ISO image.

### Usage
Just run the `./go.sh` script from the 'iso' folder and then copy the resulting image that should
be located at `data/ubuntu24_fsd_autoinstall.iso` into the XAAS NAS share:
`smb://nassvmmix01.epfl.ch/si_vsissp_iso_priv_repo_p01_app/ITServices/its_wbhst`
The share must be mounted via samba with your gaspar username/password 
from 
`smb://nassvmmix01.epfl.ch/si_vsissp_iso_priv_repo_p01_app/ITServices/its_wbhst`

### Requirements:
The only unusual tool needed is `xorriso`:

```
# on debian:
sudo apt install xorriso
sudo apt install 7zip

# on mac:
brew install xorriso
brew install 7zip
```

### NOTE
This script have been tested only on an early version. In particular, 
the `nonet` version have never been tested.
