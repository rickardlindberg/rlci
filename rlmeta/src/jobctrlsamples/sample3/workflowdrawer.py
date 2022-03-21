import os

REPLACEMENT_TAG = "$NODE-LIST$"
GREEN = '"#B2FEB2"'
YELLOW = '"#FDFEB2"'
RED = '"#F63E3E"'

class WorkflowDrawer:

    def __init__(self, tasks):
        self._tasks = tasks
        self._text = self._create_text()
        self._img = None

    def _create_text(self):
        """Create a digraph in DOT format."""
        self._ending_tasks = []
        collector = ["digraph {"]
        collector.append(f'Start[fillcolor={GREEN},style=filled];')
        collector.append('Stop[fillcolor=white,style=filled];')
        has_dependants = set()
        collector.append(REPLACEMENT_TAG)
        for t in self._tasks:
            if len(t.original_waits) == 0:
                #    start -> T2;
                collector.append(f"Start -> {t.name};")
                has_dependants.add(t.name)
            else:
                for d in t.original_waits:
                    collector.append(f'{d} -> {t.name};')
                    has_dependants.add(d)
        for t in self._tasks:
            if t.name not in has_dependants:
                collector.append(f"{t.name} -> Stop;")
                self._ending_tasks.append(t)
        collector.append("}")
        return '\n'.join(collector)

    def draw(self, done=False):
        """Create a digraph in DOT format."""
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        os.chdir(dname)
        collector = []
        for t in self._tasks:
            # T2[label="T2.Remove old build dir"];
            collector.append(f'{t.name}[label="{t.name}.{t.description}",fillcolor={t.fillcolor},style=filled,URL="{t.url}"];')
        t = f"//copy\n{self._text}"
        tt = t.replace(REPLACEMENT_TAG, "\n".join(collector))
        if done:
            if len([t for t in self._ending_tasks if t.failed]) > 0:
                tt = tt.replace("Stop[fillcolor=white,style=filled];", f"Stop[fillcolor={RED},style=filled];")
            elif len([t for t in self._ending_tasks if t.skipped]) > 0:
                tt = tt.replace("Stop[fillcolor=white,style=filled];", f"Stop[fillcolor={YELLOW},style=filled];")
            else:
                tt = tt.replace("Stop[fillcolor=white,style=filled];", f"Stop[fillcolor={GREEN},style=filled];")
        with open("sample1.txt", "w") as f:
            f.write(tt)
        os.system("dot sample1.txt -Tsvg -osample1.svg")
