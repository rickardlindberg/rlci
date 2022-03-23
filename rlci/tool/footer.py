if __name__ == "__main__":
    import sys
    import os
    path = sys.argv[1]
    with open(path) as f:
        dot = (compile_chain([
            (Parser, "file"),
            (ToDag, "asts"),
            (ToDot, "asts"),
        ], f.read()))
    dot_path = os.path.splitext(path)[0]+".dot"
    with open(dot_path, "w") as f:
        f.write(dot)
        print(f"Wrote {dot_path}:")
        print("")
        print("".join("    "+x for x in dot.splitlines(True)))
