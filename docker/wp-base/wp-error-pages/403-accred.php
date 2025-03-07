<?php

// Message shown for the "accred" error type.

$right = htmlentities($_GET["right"]);
$unit_id = htmlentities($_GET["unit_id"]);
$unit_label = htmlentities($_GET["unit_label"]);

?>

<p>
  To access this page you need the right
  <strong><?php echo $right ?></strong> in unit <strong><?php echo $unit_label ?></strong>.
</p>

<p>
  Please contact your accreditor to get access.
</p>

<ul>
  <li><a href="https://accreditation.epfl.ch">
      Accreditation FAQ
    </a></li>
</ul>
