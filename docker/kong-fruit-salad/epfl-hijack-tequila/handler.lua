-- WordPress Tequila hijack plugin for Kong
--
-- This Kong Lua handler is the `epfl-rewrite-hostnames` of
-- https://github.com/epfl-si/wordpress.plugin.tequila . It patches
-- things up when the origin server (e.g. a WordPress Deployment on
-- Kubernetes) needs to be tricked into serving out of a different
-- hostname (e.g. for A/B testing).
--
-- When the origin server wants to redirect to Tequila, this handler
-- intervenes and redirects to Tequila alright... except it does so in
-- a hijacked session it creates on the fly, in which it tells Tequila
-- to redirect to the original (request's) hostname when done.
--
-- This handler only sees the final `Location:` response header that
-- (the Tequila plugin within) the origin server emits. It is not in a
-- position to intercept the server-to-server `/cgi-bin/tequila/createrequest`
-- call, and therefore it needs to take a guess (aided by the Kong
-- configuration file) as regards which parameters to put into the hijacked
-- session.

local kong = kong
local ngx = ngx
local table = table
local string = string

local http = require("resty.http")

local EpflHijackTequila = {
  PRIORITY = 800,
  VERSION = "1.0",
}

---Redirect to *another* Tequila authentication interstitial (`/requestauth`),
---fitted with the proper hostname to redirect to afterwards.
function EpflHijackTequila:hijack_tequila (conf, kong)
  local httpc = http.new()
  local headers = {
    ["User-Agent"] = "kong-fruit-salad, inc. Tequila proxy",
  }

  local uri_path = kong.request.get_path_with_query()
  local param_sep = uri_path:match("?") and "&" or "?"
  local response, err = httpc:request_uri(
    "https://tequila.epfl.ch/cgi-bin/tequila/createrequest", {
      method = "POST",
      headers = headers,
      body = string.format([[mode_auth_check=1
allowedrequesthosts=%s
service=%s
request=%s
urlaccess=https://%s%s%sback-from-Tequila=1
]],
                   conf.allowedrequesthosts,
                   conf.service,
                   table.concat(conf.request, "+"),
                   ngx.ctx.hostname_orig, uri_path, param_sep)
  })
  if err then
    ngx.log(ngx.ERROR, err)
    return
  end

  local tequila_key
  for s in response.body:gmatch("key=%w+") do
    local tequila_redirect = string.format(
      "https://tequila.epfl.ch/cgi-bin/tequila/requestauth?requestkey=%s",
      s:sub(5))
    kong.response.set_header("Location", tequila_redirect)
    return
  end

  ngx.log(ngx.ERROR, "Did not find key in Tequila response: ", response.body)
end

function EpflHijackTequila:response (conf)
  if not ngx.ctx.hostname_orig then
    ngx.ctx.hostname_orig = kong.request.get_host()
  end

  local location = kong.response.get_header("Location")
  if location and location:match("https://tequila%.epfl%.ch") then
    self:hijack_tequila(conf, kong)
  end
end

return EpflHijackTequila
