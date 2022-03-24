def cmd_dotty(path):
    with open(path) as f:
        subprocess.run(
            ["dotty", "-"],
            encoding="utf-8",
            input=compile_chain([
                (Parser, "file"),
                (ToDag, "asts"),
                (ToDot, "asts"),
            ], f.read())
        )

def cmd_debug_dag(path):
    with open(path) as f:
        compile_chain([
            (Parser, "file"),
            (ToDag, "asts"),
        ], f.read(), debug=True)

if __name__ == "__main__":
    compile_chain([(Cli, "interpret")], sys.argv[1:], {
        "cmd_dotty": cmd_dotty,
        "cmd_debug_dag": cmd_debug_dag,
    })
