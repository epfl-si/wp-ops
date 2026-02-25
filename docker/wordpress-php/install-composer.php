<?php

chdir('/tmp');
copy('https://getcomposer.org/installer', 'composer-setup.php');

require('./composer-setup.php');
unlink('composer-setup.php');
