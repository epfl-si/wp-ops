 <?php

  // Debug informations for the 403 page.

  $ip_info = "${request_ip} (${ip_v}, ${is_inside_epfl_string})"

  ?>

 <table style="margin-top:2em; margin-bottom:2em;">
   <tr>
     <th>Request ID</th>
     <td><?php echo $request_id ?></td>
   </tr>
   <tr>
     <th>Request URI</th>
     <td><?php echo htmlentities($request_uri) ?></td>
   </tr>
   <tr>
     <th>Remote IP</th>
     <td><?php echo $ip_info ?></td>
   </tr>
 </table>
