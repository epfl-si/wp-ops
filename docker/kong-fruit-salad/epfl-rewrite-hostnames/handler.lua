-- hostname request / response rewriter plugin for Kong

local kong = kong
local ngx = ngx

local EpflRewriteHostnames = {
  PRIORITY = 800,
  VERSION = "1.0",
}

local function gsub_verbatim (str, from, to)
  from = from:gsub("([^%w])", "%%%1")
  return str:gsub(from, to)
end

local function string_starts_with (that, start)
    return that:sub(1, #start) == start
end


function EpflRewriteHostnames:access (conf)
  if not ngx.ctx.hostname_orig then
    ngx.ctx.hostname_orig = kong.request.get_host()
  end

  kong.service.request.set_header("Host", conf.hostname_inside)
end

function EpflRewriteHostnames:header_filter (conf)
  if not ngx.ctx.hostname_orig then
    ngx.ctx.hostname_orig = kong.request.get_host()
  end

  local location = kong.response.get_header("Location")
  if location then
    location = gsub_verbatim(location,
                             conf.hostname_inside,
                             ngx.ctx.hostname_orig)
    kong.response.set_header("Location", location)
  end
end

function EpflRewriteHostnames:body_filter (conf)
  local content_type = kong.response.get_header("Content-Type")

  ngx.log(ngx.DEBUG, "content_type is ", content_type)
  if content_type and (string_starts_with(content_type, "text/html")
                       or string_starts_with(content_type, "text/javascript")
                       or string_starts_with(content_type, "application/javascript")
                       or string_starts_with(content_type, "text/css")
                       or content_type == "application/json") then
    ngx.log(ngx.DEBUG, "rewriting from ", conf.hostname_inside, " to ", ngx.ctx.hostname_orig)
    local chunk, eof = ngx.arg[1], ngx.arg[2]
    if chunk ~= "" then
      chunk = gsub_verbatim(chunk, conf.hostname_inside, ngx.ctx.hostname_orig)
      ngx.arg[1] = chunk
    end
  end
end

return EpflRewriteHostnames
