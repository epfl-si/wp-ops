<?php

$ip_info = "$request_ip ($ip_v, $is_inside_epfl_string)"

?>

<table style="margin-top:2em; margin-bottom:2em;">
  <?php if ($request_id) { ?>
    <tr>
      <th style="margin-right: 2em;">Request ID</th>
      <td><?php echo $request_id ?></td>
    </tr>
  <?php } ?>
  <?php if ($_SERVER["HTTP_REFERER"]) { ?>
    <tr>
      <th style="width: 6em;">Request URI</th>
      <td><?php echo htmlentities(explode("?", $_SERVER["HTTP_REFERER"])[0]); ?></td>
    </tr>
  <?php } ?>
  <?php if ($error_type && $stx != "50x") { ?>
    <tr>
      <th style="width: 6em;">Error type</th>
      <td><?php echo $error_type ?></td>
    </tr>
  <?php } ?>
</table>
