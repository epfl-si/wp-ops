#!/bin/bash

CONFIG_FILE="/config/redirects.txt"
NGINX_CONF="/etc/nginx/nginx.conf"

echo "Generating optimized nginx config from $CONFIG_FILE"

# Base nginx config with map
cat > $NGINX_CONF << 'EOF'
worker_processes auto;
error_log stderr notice;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /dev/stdout main;
    sendfile on;
    keepalive_timeout 65;

    # Map for redirects - much more efficient than multiple server blocks
    map $host $redirect_destination {
        default "";
EOF

if [ -f "$CONFIG_FILE" ]; then
    echo "Reading redirects from $CONFIG_FILE"
    
    count=0
    while IFS=':' read -r source destination; do
        [[ -z "$source" || "$source" =~ ^[[:space:]]*# ]] && continue
        source=$(echo "$source" | xargs)
        destination=$(echo "$destination" | xargs)
        
        echo "Adding redirect: $source -> $destination"
        
        # Add map entry
        echo "        $source $destination;" >> $NGINX_CONF
        ((count++))
    done < "$CONFIG_FILE"
    
    echo "Added $count redirects to map"
else
    echo "Config file not found, using default"
    echo "        test.local example.com;" >> $NGINX_CONF
fi

# Close map and add single server block
cat >> $NGINX_CONF << 'EOF'
    }

    # Single server block handles all redirects
    server {
        listen 80;
        server_name _;
        
        # Health endpoint
        location = /health {
            return 200 'OK';
            add_header Content-Type text/plain;
        }
        
        # Reload endpoint (dummy for compatibility)
        location = /reload {
            return 200 'Map-based config active';
            add_header Content-Type text/plain;
        }
        
        # Main redirect logic
        location / {
            # If we have a redirect destination, do it
            if ($redirect_destination != "") {
                return 301 https://$redirect_destination$request_uri;
            }
            
            # No redirect configured
            return 200 'Nginx Redirect Server - No redirect configured for host: $host';
            add_header Content-Type text/plain;
        }
    }
}
EOF

echo "Generated optimized nginx config with map"

# Test config
nginx -t
