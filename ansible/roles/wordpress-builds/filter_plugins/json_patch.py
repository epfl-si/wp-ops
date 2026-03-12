import copy

class FilterModule(object):
    """Poor man's JSON Patch functionality

    ChatGPT vibe-coded."""

    def filters(self):
        return {
            "json_patch": self.json_patch,
        }

    def _resolve(self, doc, pointer):
        parts = [p for p in pointer.split("/") if p]
        cur = doc
        for p in parts[:-1]:
            if isinstance(cur, list):
                cur = cur[int(p)]
            else:
                cur = cur[p]
        return cur, parts[-1]

    def json_patch(self, doc, patch):
        doc = copy.deepcopy(doc)

        for op in patch:
            parent, key = self._resolve(doc, op["path"])

            if op["op"] == "replace":
                parent[key] = op["value"]

            elif op["op"] == "add":
                if isinstance(parent, list):
                    if key == "-":
                        parent.append(op["value"])
                    else:
                        parent.insert(int(key), op["value"])
                else:
                    parent[key] = op["value"]

            elif op["op"] == "remove":
                if isinstance(parent, list):
                    parent.pop(int(key))
                else:
                    del parent[key]

            else:
                raise ValueError(f"Unsupported op {op['op']}")

        return doc
