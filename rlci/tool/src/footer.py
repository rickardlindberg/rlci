def cmd_dotty(path):
    with open(path) as f:
        subprocess.run(
            ["dotty", "-"],
            encoding="utf-8",
            input=compile_chain([
                (Parser, "file"),
                (ToDag, "asts"),
                (ToDot, "asts"),
            ], f.read(), debug=True)
        )

def cmd_compile(path):
    with open(path) as f:
        print(json.dumps(compile_chain([
            (Parser, "file"),
            (ToDag, "asts"),
        ], f.read(), debug=True)))

def cmd_debug_dag(path):
    with open(path) as f:
        compile_chain([
            (Parser, "file"),
            (ToDag, "asts"),
        ], f.read(), debug=True)

def cmd_get_stage_definition(pipeline, stage_id):
    with open(pipeline) as f:
        print(json.dumps(compile_chain([
            (Parser, "file"),
            (ToDag, "asts"),
        ], f.read(), debug=True)[0][2+stage_id][3]))

def cmd_run(args):
    try:
        print(json.dumps(["Result", "success", compile_chain(
            [
                (StageRunner, "run"),
            ],
            json.load(sys.stdin),
            {
                "args": args,
                "sh": sh,
            },
            debug=True
        )]))
    except Exception as e:
        print(json.dumps(["Result", "failure", str(e)]))

def sh(command):
    last_stdout = ""
    process = create_process_sh(command)
    for x in stream_process(process):
        if x[0:2] == ["Log", "stdout"]:
            last_stdout = x[2]
        print(json.dumps(x))
    process.wait()
    if process.returncode != 0:
        raise ProcessFailure(f"Non-zero exit code: {process.returncode}.")
    return last_stdout

def create_process_sh(command):
    try:
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
            errors="replace"
        )
    except Exception as e:
        raise ProcessFailure(f"Unable to create process: {e}.")

class ProcessFailure(Exception):
    pass

def stream_process(process):
    def reader(output, stream, name):
        try:
            for line in stream:
                output.put(["Log", name, line.rstrip("\n")])
        finally:
            output.put(["end", name])
    output = queue.Queue()
    ends = ["stdout", "stderr"]
    threading.Thread(target=reader, args=(output, process.stdout, "stdout")).start()
    threading.Thread(target=reader, args=(output, process.stderr, "stderr")).start()
    while ends:
        item = output.get()
        if item[0] == "end":
            ends.remove(item[1])
        else:
            yield item

if __name__ == "__main__":
    compile_chain([(Cli, "interpret")], sys.argv[1:], {
        "cmd_dotty": cmd_dotty,
        "cmd_compile": cmd_compile,
        "cmd_debug_dag": cmd_debug_dag,
        "cmd_get_stage_definition": cmd_get_stage_definition,
        "cmd_run": cmd_run,
    })
