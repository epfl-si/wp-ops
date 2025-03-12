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
      <th style="width: 8em;">Request URI</th>
      <?php if ($_SERVER["STATUS"] == 403) { ?>
        <td><?php echo htmlentities(explode("?", $_SERVER["HTTP_REFERER"])[0]); ?></td>
      <?php } else { ?>
        <td><?php echo htmlentities($_SERVER["HTTP_REFERER"]); ?></td>
      <?php } ?>
    </tr>
  <?php } ?>
  <?php if ($error_type && $stx != "50x") { ?>
    <tr>
      <th style="width: 8em;">Error type</th>
      <td><?php echo $error_type ?></td>
    </tr>
  <?php } ?>
</table>
