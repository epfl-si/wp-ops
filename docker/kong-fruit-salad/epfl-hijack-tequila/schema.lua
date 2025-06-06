return {
  name = "epfl-hijack-tequila",
  fields = {
    { config = {
        type = "record",
        fields = {
          { allowedrequesthosts  = { type = "string", required = true }, },
          { service              = { type = "string", required = true }, },
          { request              = { type = "array",  required = true,
                                     elements = {type = "string"},    }, },
        },
    }, },
  }
}
