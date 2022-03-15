if __name__ == "__main__":
    import sys
    import os
    with open(sys.argv[1]) as f:
        dot = (compile_chain([
            (Parser, "file"),
            (ToDag, "asts"),
            (ToDot, "asts"),
        ], f.read()))
    with open(os.path.splitext(sys.argv[1])[0]+".dot", "w") as f:
        f.write(dot)
        print(dot)
