return {
  name = "epfl-rewrite-hostnames",
  fields = {
    { config = {
        type = "record",
        fields = {
          { hostname_inside = { type = "string", required = true }, },
        },
    }, },
  }
}
